import datetime

# internal
from dash_access.clients.base import BaseAccessStore
from dash_access.access.relationship import Args, create, delete, delete_all, exists, get_all, copy

def duplicate(store: BaseAccessStore, name: str, new_name: str) -> bool:
    # duplicate the relationships
    copy(
        from_principal=name,
        from_principal_type="group",
        to_principal=new_name,
        to_principal_type="group"
    )
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
        args = Args(x,"user",name,"group")
        if not exists(store, args):
            create(store, args)

    # DEFINE THE GROUP-GROUP INHERITS RELATIONSHIPS
    add_inherits(store, name, inherits=inherits)
    return True


def add_inherits(store: BaseAccessStore, name: str, inherits: list = []) -> bool:
    for gname in inherits:
        args = Args(name,"group",gname,"group")
        if not exists(store,args):
            create(store, args)
    return True


def remove_inherits(store: BaseAccessStore, name: str, remove: list = []) -> bool:
    for gname in remove:
        delete(store, Args(name,"group",gname,"group"))
    return True


def add_permissions(store: BaseAccessStore, name: str, permissions: list = []) -> bool:
    for x in permissions:
        args = Args(name,"group",x,"permission")
        if not exists(store,args):
            create(store, args)
    return True


def remove_permissions(
    store: BaseAccessStore, name: str, permissions: list = []
) -> bool:
    for x in permissions:
        delete(store,Args(name,"group",x,"permission"))
    return True


def add_users(store: BaseAccessStore, name: str, users: list = []) -> bool:
    for x in users:
        args = Args(x,"user",name,"group")
        if not exists(store,args):
            create(store,args)
    return True


def remove_users(store: BaseAccessStore, name: str, users: list = []) -> bool:
    for x in users:
        delete(store,Args(x,"user",name,"group"))
    return True


def inherits(store: BaseAccessStore, name: str, already: list = []) -> list:
    """
    grab all the groups inherited by group <name>
    stop an infinite inheritance loop by passing in <already> - a list of groups the function has already seen
    returns None if name does not exist
    """
    this_inherits = inherits(store,name)
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
    this_group_permissions = get_all(store,Args(name,"group",granted_type="permission"))

    groups = inherits(store, name)
    permissions = []
    for gname in groups:
        gpermissions = get_all(store,Args(gname,"group",granted_type="permission"))
        permissions.extend(gpermissions)
    permissions = list(set([*permissions, *this_group_permissions]))
    return permissions
