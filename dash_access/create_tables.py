import datetime
import sqlite3

from dash_access.access import group, relationship
from dash_access.auth import pw
from dash_access.clients.sqlite3 import Sqlite3AccessStore

def tables():
    return {
    "access_events": """
        create table if not exists access_events (
            email text,
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
    "login_events": """
        create table if not exists login_events (
            email text,
            action text,
            ts text,
            status bool,
            reason text
    )""",
    "groups": """
        create table if not exists groups (
            id text primary key,
            inherits blob,
            update_ts text
        )
    """,
    "relationships": """
        create table if not exists relationships (
            id text,
            principal text,
            principal_type text,
            granted text,
            granted_type text,
            ts text
    )""",
}


def create_dev_tables(path: str = "./local.sqlite3"):
    ###########################################################################
    ## create local tables
    ###########################################################################
    with sqlite3.connect(path) as con:
        cur = con.cursor()
        for t,v in tables().items():
            cur.execute(v)
        con.commit()


def drop_dev_tables(path: str = "./local.sqlite3"):
    with sqlite3.connect(path) as con:
        cur = con.cursor()
        for t in tables():
            cur.execute(f"drop table if exists {t}")


groups = [
    dict(name="entry",permissions=['open']),
    dict(name="mid",permissions=["sensitive"],inherits=["entry"]),
    dict(name="top", permissions=["classified",], inherits=["mid"]),
    dict(name="all", permissions=["*"]),
    dict(name="test-users"),
]

users = [
    dict(email="employee", groups=["entry"], password="test"),
    dict(email="manager", groups=["mid"], password="test"),
    dict(email="executive", groups=["top"], password="test"),
    dict(email="admin", groups=["all"], password="test"),
]

def create_values():
    ###########################################################################
    ## insert example users into local tables
    ###########################################################################
    store = Sqlite3AccessStore(path="local.sqlite3")
    for gg in groups:
        group.add(store,**gg)
    for uu in users:
        for g in uu['groups']:
            relationship.user_group_create(store, uu['email'],g)


def create():
    create_dev_tables()
    create_values()

def drop():
    ###########################################################################
    ## drop example users from local dev tables
    ###########################################################################
    all_groups = group.get_all()
    for gg in all_groups:
        group.delete(gg["name"])

    all_users = user.get_all()
    for uu in all_users:
        user.delete(uu["email"])