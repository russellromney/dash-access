# external imports
import functools
import msgpack
import sqlite3
import os
import decimal
from boto3.dynamodb.types import Binary
import datetime

from dash_access.clients.base import BaseAccessStore


def tables():
    return {
        "access_events": """
        create table if not exists access_events (
            user_id text,
            permission text,
            ts text,
            status bool
        )""",
        "admin_events": """
        create table if not exists admin_events (
            ts text,
            table_name text,
            operation text,
            vals blob,
            where_val blob
        )""",
        "relationships": """
        create table if not exists relationships (
            id text,
            principal text,
            principal_type text,
            granted text,
            granted_type text,
            ts text
        )
        """,
    }


def create_tables(db):
    cur = db.cursor()
    for k, v in tables().items():
        cur.execute(v)
        db.commit()
        print("CREATED SQLITE3 TABLE:", k)
    cur.close()
    return True


def drop_tables(db):
    cur = db.cursor()
    for t in tables():
        cur.execute(f"drop table if exists {t}")
        db.commit()
        print("DROPPED SQLITE3 TABLE:", t)
    cur.close()
    return True


def admin_log(func):
    """
    whenever something is added, deleted, or changed,
    log the event to the admin database

    wrapped function must return two things:
    the operation (dict) and the actual output
    this logs the operation to the admin table and returns the actual result
    """

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        table, operation, values, where, out = func(self, *args, **kwargs)
        # LOG TO ADMIN EVENTS LOG
        table = self.get_table("admin_events")
        with self.get_db() as db:
            cursor = db.cursor()
            statement = f"""
                insert into {table} (ts, table_name, operation, vals, where_val)
                values (?,?,?,?,?)
            """
            cursor.execute(
                statement,
                (
                    datetime.datetime.now().isoformat(),
                    table,
                    operation,
                    msgpack.dumps(values),
                    msgpack.dumps(where),
                ),
            )
            db.commit()
        return out

    return wrapper


class Sqlite3AccessStore(BaseAccessStore):
    """
    reference a persistent local store for development and some testing

    not recommended to use this for real developement.
    e.g. set the db with some env-dependent logic when creating the app, like
        if os.environ.get("ENV") == "DEV":
            setup_dev_db() # some function that sets up dev tables etc.
            args = ["/path/to/db"]
            env_access_store = Sqlite3AccessStore
            class User:
                __tablename__ = "dev_users"
                __access_store__ = env_access_store(*args)
                ...
        elif os.environ.get("ENV") == "STAGE":
            setup_stage_db() # some function that sets up stage tables etc.
            db = SQLAlchemy(someURI) # this would be somewhere else
            args = [db]
            env_access_store = PostgresAccessStore
            class User:
                __tablename__ = "stage_users"
                __access_store__ = env_access_store(*args)
                ...
    """

    def __init__(self, path: str = "local.db"):
        self.instantiate(path)

    def get_db(self):
        return self.db

    @property
    def db(self):
        # can't share connections between threads - new connection for each transaction
        # fix this by using custom logic to share connectinos between threads with flask.g
        # this isn't normal as you should use a production database with SqlAlchemy or DynamoDB, not Sqlite.
        # Only should only be used for dev.
        con = sqlite3.connect(self.path)
        con.row_factory = sqlite3.Row  # return values as dicts
        cur = con.cursor()
        cur.execute("PRAGMA journal_mode = WAL")
        cur.execute("PRAGMA synchronous = NORMAL")
        con.commit()
        cur.close()
        return con

    def instantiate(self, path: str = "local.db"):
        """instantiate with sqlite3 as the backing store"""
        self.path = path

    def get_table(self, table):
        tables = {
            "users": os.environ.get("USERS_TABLE", "users"),
            "relationships": os.environ.get("RELATIONSHIPS_TABLE", "relationships"),
            "admin_events": os.environ.get("ADMIN_EVENTS_TABLE", "admin_events"),
            "access_events": os.environ.get(
                "LOGGING_TABLE_ACCESS_EVENTS", "access_events"
            ),
        }
        out = tables.get(table)
        if not table:
            raise ValueError(
                f"get_table: table must be one of {', '.join(tables.keys())}"
            )
        return out

    def _decode(self, x):
        if isinstance(x, bytes):
            return msgpack.loads(x)
        return x

    def _encode(self, x):
        if isinstance(x, dict) or isinstance(x, list):
            return msgpack.dumps(x)
        return x

    def _get(self, key: str, table: str) -> dict:
        """
        key:
            str, int, float

        note on types:
            if value was a dictionary, it transforms back to dictionary and loads
            if value was a int, float, just returns the original value

        returns:
            The value for the key in the store
            None if key does not exist

        NOTE this simplifies everything by returning the entire record
            every time, with default values for missing fields. Otherwise we'd have to do some custom logic.
            It's easier to expect a full record and handle errors later.
        """
        table_fields = self.table_fields(table)

        cur = self.db.cursor()
        val = cur.execute(
            f"""select * from {self.get_table(table)} where id=?""", (key,)
        ).fetchone()

        out = val
        if val is not None:
            out = dict(out)
            out = {k: self.decode(v) for k, v in out.items()}

            # ADD DEFAULT FIELD VALUES FOR MISSING FIELDS
            for field in table_fields:
                if not field in out:
                    out[field] = table_fields[field]

        return out

    def _get_all(self, table: str, where: list = None) -> list:
        """
        get all the values from a given table

        where:
            can add a WHERE statement
            only AND is allowed
            [
                {
                    "col": string,
                    "val": string | int | float | bool
                }
            ]
        """
        table_fields = self.table_fields(table)
        cur = self.db.cursor()

        if not where in (None, []):
            statement = (
                f"""select * from {self.get_table(table)} where {where[0]["col"]} = ?"""
            )
            ands = " ".join([f"""and {x['col']} = ?""" for x in where[1:]])
            statement += ands
            inputs = tuple([x["val"] for x in where])
            val = cur.execute(statement, inputs).fetchall()
        else:
            statement = f"""
                select * from {self.get_table(table)}
            """
            val = cur.execute(statement).fetchall()
        if not val:
            return []
        out = [{key: self.decode(value) for key, value in dict(d).items()} for d in val]

        # ADD DEFAULT FIELD VALUES FOR MISSING FIELDS
        for o in out:
            for field in table_fields:
                if not field in o:
                    out[field] = table_fields[field]
        return out

    @admin_log
    def _set(self, key: str, table: str, val: dict) -> bool:
        """
        key:
            str
        val:
            str, int, float, dict, list, tuple

        notes on types:
            datatypes are handled with self.encode()

        returns:
            True if val successfully stored
            False otherwise
        """
        # SELECT TABLE
        this_table = self.get_table(table)

        # PROCESS VALUES - NO DYNAMO TYPES
        out = {key: self.encode(value) for key, value in val.items()}
        out = {
            key: (float(value) if isinstance(value, decimal.Decimal) else value)
            for key, value in out.items()
        }

        ###########################################################
        ## INSERT OR UPDATE THE RECORD IN THE DATABASE
        with self.get_db() as db:
            cur = db.cursor()

            # IF THE RECORD EXISTS, UPDATE IT
            if cur.execute(f"select * from {this_table} where id=?", (key,)).fetchone():
                # EXCLUDE id FOR UPDATES
                ID = out["id"]
                out = {k: v for k, v in out.items()}
                statement = f"""update {this_table} set {','.join([f'{col}=?' for col in out])} where id=?"""
                cur.execute(statement, tuple([*out.values(), ID]))

            # OTHERWISE INSERT THE NEW RECORD
            else:
                statement = f"""insert into {this_table} ({','.join(out.keys())}) values ({','.join(['?' for y in out])})"""
                cur.execute(statement, tuple(out.values()))
            db.commit()
            cur.close()
        ## DONE
        ###########################################################
        return this_table, "set", out, None, True

    @admin_log
    def _delete(self, key: str, table: str, where: list = None) -> bool:
        """
        delete from the table
        where optional

        where:
            can add a WHERE statement
            where statements function as ANDs
            [
                {
                    "col": string,
                    "val": string | int | float | bool
                }
            ]
        """
        # SELECT TABLE
        this_table = self.get_table(table)

        # PUT THE VALUE
        with self.get_db() as db:
            cur = db.cursor()
            if not where in (None, []):
                statement = f"""delete from {self.get_table(table)} where {where[0]["col"]} = ?"""
                ands = " ".join([f"""and {x['col']} = ?""" for x in where])
                statement += ands
                inputs = tuple([x["val"] for x in where])
                cur.execute(statement, inputs)
            else:
                cur.execute(f"""delete from {this_table} where id=?""", (key,))
            cur.close()
            db.commit()

        return this_table, "delete", key, where, True

    def _insert(self, table, **kwargs):
        """
        insert values into a logging table
        table name must exist (duh)
        kwargs is column names mapped to values
        """
        # SELECT TABLE
        this_table = self.get_table(table)

        # PROCESS VALUES - UNDO DYNAMO DATA TYPES
        out = {key: self.encode(value) for key, value in kwargs.items()}
        out = {
            key: (float(value) if isinstance(value, decimal.Decimal) else value)
            for key, value in out.items()
        }
        out = {
            key: (value.value if isinstance(value, Binary) else value)
            for key, value in out.items()
        }

        with self.get_db() as db:
            cur = db.cursor()
            cur.execute(
                f"""insert into {this_table} ({ ','.join(out.keys()) }) values ({ ','.join(['?' for x in out]) })""",
                tuple(out.values()),
            )
            cur.close()
            db.commit()
        return True

    def create_tables(self):
        return create_tables(self.db)

    def drop_tables(self):
        return drop_tables(self.db)
