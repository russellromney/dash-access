
# external imports
from typing import Iterable
import functools
import msgpack
import psycopg2
import os
import decimal
from boto3.dynamodb.types import Binary
from functools import wraps
import datetime

from dash_access.clients.base import BaseAccessStore

def tables():
    return {
        "access_events": """
            create table if not exists access_events (
                user_id varchar (50),
                permission varchar (50),
                ts varchar (50),
                status boolean
            );
        """,
        "admin_events": """
            create table if not exists admin_events (
                ts varchar  (50),
                table_name varchar  (50),
                operation varchar (50),
                vals bytea,
                where_val bytea
            );
        """,
        "groups": """
            create table if not exists groups (
                id varchar (50),
                update_ts varchar (50)
            );
        """,
        "relationships": """
            create table if not exists relationships (
                id varchar (50) ,
                principal varchar (50),
                principal_type varchar (50),
                granted varchar (50) ,
                granted_type varchar (50),
                ts varchar (50) 
            );
        """,
    }

def create_tables(db):
    cur = db.cursor()
    for k,v in tables().items():
        cur.execute(v)
        db.commit()
        print("CREATED POSTGRES TABLE:",k)
    cur.close()
    return True

def drop_tables(db):
    cur = db.cursor()
    for t in tables():
        cur.execute(f"drop table if exists {t}")
        db.commit()
        print("DROPPED POSTGRES TABLE:",t)
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
    def wrapper(self,*args,**kwargs):
        table, operation, values, where, out = func(self, *args,**kwargs)
        # LOG TO ADMIN EVENTS LOG
        table = self.get_table("admin_events")
        cursor = self.db.cursor()
        statement = f"""
            insert into {table} (ts, table_name, operation, vals, where_val)
            values (%s,%s,%s,%s,%s)
        """
        cursor.execute(
            statement, 
            (
                datetime.datetime.now().isoformat(),
                table,
                operation,
                msgpack.dumps(values),
                msgpack.dumps(where),
            )
        )
        self.db.commit()
        return out
    return wrapper


class PostgresAccessStore(BaseAccessStore):
    """
    reference a persistent local store for development and some testing

    uses sqlite3 to mock DynamoDB interaction
    """
    def __init__(self, db):
        self.instantiate(db)

    def get_db(self):
        return self.db

    def instantiate(self, db):
        """instantiate with postgres as the backing store"""
        print("INSTANTIATING POSTGRES ACCESS DB")
        self.db = db

    def get_table(self, table):
        tables = {
            "users": os.environ.get("USERS_TABLE", 'users'),
            "groups": os.environ.get("GROUPS_TABLE", "groups"),
            "relationships": os.environ.get("RELATIONSHIPS_TABLE",'relationships'),
            "admin_events": os.environ.get("ADMIN_EVENTS_TABLE",'admin_events'),
            "access_events": os.environ.get("LOGGING_TABLE_ACCESS_EVENTS","access_events"),
        }
        out = tables.get(table)
        if not table:
            raise ValueError(
                f"get_table: table must be one of {', '.join(tables.keys())}"
            )
        return out

    def _decode(self, x):
        if isinstance(x, memoryview):
            return msgpack.loads(x.tobytes())
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
        cur.execute(
            f"""
            select * from {self.get_table(table)}
            where id = %s
        """,
            (key,),
        )
        out = cur.fetchall()
        cur.close()

        if isinstance(out, Iterable) and len(out)==0:
            return []
        if out is not None and out != [()]:
            out = dict(out)
            out = {k: self.decode(v) for k, v in out.items()}

            # ADD DEFAULT FIELD VALUES FOR MISSING FIELDS
            for field in table_fields:
                if not field in out:
                    out[field] = table_fields[field]
        else:
            out = None
        return out
    
    def _get_all(self, table: str, where: list=None) -> list:
        """
        get all the values from a given table
        
        where:
            can add a WHERE statement
            only AND is allowed
            [
                {
                    "col": string,
                    "val": string | int | float | boolean
                }
            ]
        """
        table_fields = self.table_fields(table)

        cur = self.db.cursor()
        
        if not where in (None, []):
            statement = f"""
                select * from {self.get_table(table)}
                where {where[0]["col"]} = %s
            """
            ands = " ".join(
                [
                    f"""and {x['col']} = %s"""
                    for x in where[1:]
                ]
            )
            statement += ands
            inputs = tuple([x['val'] for x in where])
            cur.execute(
                statement,
                inputs
            )
            val = cur.fetchall()
        else:
            statement = f"""
                select * from {self.get_table(table)}
            """
            cur.execute(
                statement
            )
            val = cur.fetchall()

        if not val or val == [()]:
            return []
        out = [
            {key: self.decode(value) for key,value in zip(table_fields.keys(),d)}
            for d in val
        ]
        
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
        out = {k: self.encode(value) for k, value in val.items()}
        out = {k: (float(value) if isinstance(value, decimal.Decimal) else value) for k, value in out.items()}

        ###########################################################
        ## INSERT OR UPDATE THE RECORD IN THE DATABASE

        cur = self.db.cursor()

        # IF THE RECORD EXISTS, UPDATE IT
        cur.execute(f"select * from {this_table} where id=%s",(key,))
        temp = cur.fetchone()
        if not temp in ([],None):
            print(temp)
            # EXCLUDE id FOR UPDATES
            ID = out['id']
            out = {k: v for k, v in out.items()}
            statement = f"""
                update {this_table} 
                set {','.join([f'{col}=%s' for col in out])}
                where id = %s
            """
            cur.execute(statement, tuple([*out.values(),ID]))

        # OTHERWISE INSERT THE NEW RECORD
        else:
            statement = f"""
                insert into {this_table}
                ({','.join(out.keys())})
                values ({','.join(['%s' for y in out])})
            """
            cur.execute(statement, tuple(out.values()))
        cur.close()
        ## DONE
        ###########################################################
        return this_table, "set", out, None, True

    @admin_log
    def _delete(self, key: str, table: str, where: list=None) -> bool:
        """
        delete from the table; where optional
        
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
        # SELECT TABLE
        this_table = self.get_table(table)

        # PUT THE VALUE
        cur = self.db.cursor()
        if not where in (None, []):
            statement = f"""
                delete from {self.get_table(table)}
                where {where[0]["col"]} = %s
            """
            ands = " ".join(
                [
                    f"""and {x['col']} = %s"""
                    for x in where
                ]
            )
            statement += ands
            inputs = tuple([x['val'] for x in where])

            cur.execute(
                statement,
                inputs
            )
        else:
            cur.execute(
                f"""
                delete from {this_table}
                where id = %s
            """,
                (key,),
            )
        cur.close()

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

        db = self.db
        cur = db.cursor()
        cur.execute(
            f"""
                insert into {this_table} 
                    ({ ','.join(out.keys()) })
                values
                    ({ ','.join(['%s' for x in out]) })
            """,
            tuple(out.values()),
        )
        db.commit()
        cur.close()
        return True

    def create_tables(self):
        return create_tables(self.db)
    def drop_tables(self):
        return drop_tables(self.db)