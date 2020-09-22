# external imports
import uuid
import datetime

# local imports
from dash_access.clients.base import BaseAccessStore
from dash_access.access import relationship


def get(store: BaseAccessStore, name: str) -> dict:
    """
    pull a group's data from the store based on group name
    
    args:
        name: str
        store: the app's access store object
    
    returns:
        dict of group values if group exists
        else None
    """
    group = store.get(name, table="groups")
    if group in ([],None):
        return None
    return group


def get_all(store: BaseAccessStore) -> list:
    return store.get_all('groups')


def put(store: BaseAccessStore, name: str, record: dict) -> bool:
    """
    shortcut to setting a value in the store for groups
    """
    return store.set(key=name, table="groups", val=record)


def exists(store: BaseAccessStore, name: str):
    out = get(store, name) is not None
    return out


def add(
    store: BaseAccessStore,
    name: str,
    permissions: list = [],
    inherits: list = [],
    users: list = [],
) -> bool:
    """
    create a group in the store
    creates relationships with groups - users and permissions (if not exist)

    returns bool of success
    """
    # don't do it if the group already exists
    if exists(store, name):
        return False

    # do it
    record = {
        "id": name,
        "update_ts": datetime.datetime.now().isoformat(),
    }
    # CREATE THE GROUP
    res = put(store, name, record)
    
    # DEFINE THE GROUP-PERMISSION RELATIONSHIPS
    add_permissions(store, name, permissions=permissions)

    # DEFINE THE GROUP-USER RELATIONSHIPS
    for x in users:
        if not relationship.user_group_exists(store, x,name):
            relationship.user_group_create(store, x,name)

    # DEFINE THE GROUP-GROUP INHERITS RELATIONSHIPS
    add_inherits(store, name, inherits=inherits)

    return res


def delete(store: BaseAccessStore, name: str) -> bool:
    if exists(store, name):
        res_store = store.delete(name, table="groups")
        relationship.delete_all(store, name, "group")
        return res_store
    else:
        return True


def change_name(store: BaseAccessStore, name: str, new_name: str) -> bool:
    record = get(store, name)
    if not record:
        return False

    if exists(store, new_name):
        return False
    
    record['name'] = new_name
    put(store, name, record)
    return True


def duplicate(store: BaseAccessStore, name: str, new_name: str) -> bool:
    # does the new one already exist?
    if exists(store, new_name):
        return False

    # does the one to duplicate exist?
    if not exists(store, name):
        return None

    # add the sucker
    add(store, new_name)

    # duplicate the relationships
    relationship.group_group_copy(store, name, new_name)

    return True


def add_inherits(store: BaseAccessStore, name: str, inherits: list = []) -> bool:
    if not exists(store,name):
        return None
    for gname in inherits:
        if not relationship.group_group_exists(store, name, gname):
            relationship.group_group_create(store, name, gname)
    return True


def remove_inherits(store: BaseAccessStore, name: str, remove: list=[]) -> bool:
    if not exists(store,name):
        return None
    for gname in remove:
        relationship.group_group_delete(store, name, gname)
    return True

def add_permissions(store: BaseAccessStore, name: str, permissions: list=[]) -> bool:
    if not exists(store,name):
        return None
    for x in permissions:
        if not relationship.group_permission_exists(store, name,x):
            relationship.group_permission_create(store, name, x)
    return True


def remove_permissions(store: BaseAccessStore, name: str, permissions: list=[]) -> bool:
    if not exists(store,name):
        return None
    for x in permissions:
        relationship.group_permission_delete(store, name,x)
    return True


def add_users(store: BaseAccessStore, name: str, users: list=[]) -> bool:
    if not exists(store,name):
        return None
    for x in users:
        if not relationship.user_group_exists(store, name,x):
            relationship.user_group_create(store, name, x)
    return True


def remove_users(store: BaseAccessStore, name: str, users: list=[]) -> bool:
    if not exists(store,name):
        return None
    for x in users:
        relationship.user_group_delete(store, name, x)
    return True


def inherits(store: BaseAccessStore, name: str, already: list = []) -> list:
    """
    grab all the groups inherited by group <name>
    stop an infinite inheritance loop by passing in <already> - a list of groups the function has already seen
    returns None if name does not exist
    """
    record = get(store, name)
    if record is None:
        return already

    this_inherits = relationship.group_group_all(store, name)
    new_inherits = []
    for gname in this_inherits:
        if gname in already:
            pass
        else:
            new_inherits.extend(
                list(set([gname, *inherits(store, name=gname, already=[*already, gname])]))
            )

    out = list(set([*new_inherits, *already]))
    return out


def permissions(store: BaseAccessStore, name: str) -> list:
    """
    get all the permissions to which the group has access
    
    first, get all the groups that it can access
    then, get the list of permissions those granted collectively to those groups
    """
    record = get(store, name)
    if record is None:
        return []
    this_group_permissions = relationship.group_permission_all(store, name)

    groups = inherits(store, name)
    permissions = []
    for gname in groups:
        gpermissions = relationship.group_permission_all(store, gname)
        permissions.extend(gpermissions)
    permissions = list(set([*permissions, *this_group_permissions]))
    return permissions