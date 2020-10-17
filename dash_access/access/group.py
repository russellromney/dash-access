import datetime

# internal
from dash_access.clients.base import BaseAccessStore
from dash_access.access.relationship_objects import Grant as grant, Principal as principal

def duplicate(store: BaseAccessStore, name: str, new_name: str) -> bool:
    # duplicate the relationships
    principal.group(name).copy.group(store, new_name)

    return True

def add(
    store: BaseAccessStore,
    name: str,
    permissions: list = [],
    inherits: list = [],
    users: list = [],
) -> bool:
    """
    shortcut to add relationships and inherits for a given group
    returns bool of success
    """
    # DEFINE THE GROUP-PERMISSION RELATIONSHIPS
    add_permissions(store, name, permissions=permissions)

    # DEFINE THE GROUP-USER RELATIONSHIPS
    for x in users:
        if not grant.group(name).to.user(x).exists(store):
            grant.group(name).to.user(x).create(store)

    # DEFINE THE GROUP-GROUP INHERITS RELATIONSHIPS
    add_inherits(store, name, inherits=inherits)
    return True


def add_inherits(store: BaseAccessStore, name: str, inherits: list = []) -> bool:
    for gname in inherits:
        if not grant.group(gname).to.group(name):
            grant.group(gname).to.group(name).create(store)
    return True


def remove_inherits(store: BaseAccessStore, name: str, remove: list = []) -> bool:
    for gname in remove:
        grant.group(gname).to.group(name).delete(store)
    return True


def add_permissions(store: BaseAccessStore, name: str, permissions: list = []) -> bool:
    for x in permissions:
        if not grant.permission(x).to.group(name).exists(store):
            grant.permission(x).to.group(name).create(store)
    return True


def remove_permissions(
    store: BaseAccessStore, name: str, permissions: list = []
) -> bool:
    for x in permissions:
        grant.permission(x).to.group(name).delete(store)
    return True


def add_users(store: BaseAccessStore, name: str, users: list = []) -> bool:
    for x in users:
        if not grant.group(name).to.user(x).exists(store):
            grant.group(name).to.user(x)
    return True


def remove_users(store: BaseAccessStore, name: str, users: list = []) -> bool:
    for x in users:
        grant.group(name).to.user(x).delete(store)
    return True


def inherits(store: BaseAccessStore, name: str, already: list = []) -> list:
    """
    grab all the groups inherited by group <name>
    stop an infinite inheritance loop by passing in <already> - a list of groups the function has already seen
    returns None if name does not exist
    """
    this_inherits = grant.group(name).get.groups(store)
    new_inherits = []
    for gname in this_inherits:
        if gname in already:
            pass
        else:
            new_inherits.extend(
                list(
                    set(
                        [gname, *inherits(store, name=gname, already=[*already, gname])]
                    )
                )
            )

    out = list(set([*new_inherits, *already]))
    return out


def permissions(store: BaseAccessStore, name: str) -> list:
    """
    get all the permissions to which the group has access
    
    first, get all the groups that it can access
    then, get the list of permissions those granted collectively to those groups
    """
    this_group_permissions = principal.group(name).get.permissions(store)

    groups = inherits(store, name)
    permissions = []
    for gname in groups:
        gpermissions = principal.group(gname).get.permissions(store)
        permissions.extend(gpermissions)
    permissions = list(set([*permissions, *this_group_permissions]))
    return permissions
