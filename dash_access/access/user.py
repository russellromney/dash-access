import datetime
from typing import List

# internal
from dash_access.auth import generate_password_hash
from dash_access.access import group
from dash_access.access.relationship import Args, create, exists, delete, get_all
from dash_access.clients.base import BaseAccessStore


def add_groups(store: BaseAccessStore, user_id: str, groups: list) -> bool:
    """create user-group relationship(s)"""
    for x in groups:
        args = Args(user_id, "user", x, "group")
        if not exists(store, args):
            create(store, args)
    return True


def remove_groups(store: BaseAccessStore, user_id: str, groups: list) -> bool:
    """remove all user-group relationship(s)"""
    for x in groups:
        args = Args(user_id, "user", x, "group")
        delete(store, args)
    return True


def add_permissions(store: BaseAccessStore, user_id: str, permissions: list) -> bool:
    """create user-permission relationship(s)"""
    for x in permissions:
        args = Args(user_id, "user", x, "permission")
        create(store, args)
    return True


def remove_permissions(store: BaseAccessStore, user_id: str, permissions: list) -> bool:
    """remove user-permission relationship"""
    for x in permissions:
        args = Args(user_id, "user", x, "permission")
        delete(store, args)
    return True


def groups(store: BaseAccessStore, user_id: str) -> list:
    """get all the user-group relationships"""
    args = Args(principal=user_id, principal_type="user", granted_type="group")
    this_user_groups = get_all(store, args)

    # recursively follow each group's inheritance trail
    # add each group's trail to the user's list of groups
    for gname in this_user_groups:
        this_group_inherits = group.inherits(store, gname)
        this_user_groups.extend(this_group_inherits)

    # return a unique list of groups
    return list(set(this_user_groups))


def permissions(store: BaseAccessStore, user_id: str) -> list:
    """
    get all the direct and indirect user-permission relationships for this user

    first, get the relationships in which a group is granted to this user
    follow the group inheritance chain to get all the associated group-group relationships
    then, combine the user's direct permissions with each group's granted permissions
    return that combined list
    """
    user_permissions = get_all(store, Args(user_id, "user", granted_type="permission"))
    user_groups = get_all(store, Args(user_id, "user", granted_type="group"))

    already_fetched_groups = []
    inherited_groups = user_groups.copy()
    to_fetch = user_groups.copy()
    while to_fetch:
        this_inherited_group = to_fetch.pop(0)
        if this_inherited_group in already_fetched_groups:
            continue
        this_granted_groups = get_all(
            store, Args(this_inherited_group, "group", granted_type="group")
        )
        inherited_groups.extend(this_granted_groups)
        already_fetched_groups.append(this_inherited_group)
        to_fetch.extend(this_granted_groups)
        to_fetch = list(set(to_fetch))

    all_inherited_permissions = []
    for group in list(set(inherited_groups)):
        this_group_permissions = get_all(
            store, Args(group, "group", granted_type="permission")
        )
        all_inherited_permissions.extend(this_group_permissions)

    all_user_permissions = list(set([*user_permissions, *all_inherited_permissions]))
    return all_user_permissions


def permission_access(
    store: BaseAccessStore, user_id: str, permission: str, ts: str, status: bool
) -> bool:
    """
    log an attempt by a user to access a permission-protected asset
    event goes to the access events table
    """
    permission_insert = store.insert(
        table="access_events",
        user_id=user_id,
        permission=permission,
        ts=ts,
        status=status,
    )
    return permission_insert


def has_access(
    store: BaseAccessStore, user_id: str = None, permission: str = None
) -> bool:
    """
    does the given user have direct or indirect relationship with the permission?

    returns False if
        the user does not exist
        OR
        the user does not have direct or indirect relationship with the permission
    return True if
        the user exists
        AND
        the user has direct or indirect relationship with the permission

    first, get the permissions granted to the user
    then, get the granted to the user
    if the permission is in the user's granted permissions, they have access

    At the end, log the access attempt
    """
    if user_id is None or permission is None:
        return None

    # DOES THE USER HAVE ACCESS TO THE permission?
    user_permissions = permissions(store, user_id)
    specific_permission = permission in user_permissions
    all_permissions = "*" in user_permissions
    user_has_access = specific_permission or all_permissions

    # LOG permission ACCESS ATTEMPT
    permission_access(
        store=store,
        user_id=user_id,
        permission=permission,
        ts=datetime.datetime.now().isoformat(),
        status=user_has_access,
    )
    return user_has_access


class AccessUserMixin(object):
    """
    Simple class-based API to the dash_access.

    Add it as an attribute of the flask_login.current_user user model
    to simplify checking access control for a given user.
    e.g.
        class User:
            def __init__(self):
                ...
                self.access = UserAccess(access_db_connection, user_id)
                ...

        Then you can use it to build custom access checking logic, like:
        ...
        if current_user.access.has_access("some_permission"):
            ...
    """

    @property
    def store(self):
        return self.__access_store__

    def add_groups(self, groups: list) -> bool:
        return add_groups(self.store, self.id, groups)

    def add_group(self, name: str) -> bool:
        return self.add_groups([name])

    def remove_groups(self, groups: list) -> bool:
        return remove_groups(self.store, self.id, groups)

    def remove_group(self, name: str) -> bool:
        return self.remove_groups([name])

    def add_permissions(self, permissions: list) -> bool:
        return add_permissions(self.store, self.id, permissions)

    def add_permission(self, permission: str) -> bool:
        return self.add_permissions([permission])

    def remove_permissions(self, permissions: list) -> bool:
        return remove_permissions(self.store, self.id, permissions)

    def remove_permission(self, permission: str) -> bool:
        return self.remove_permissions([permission])

    def has_access(self, permission: str) -> bool:
        out = has_access(self.store, self.id, permission)
        return out

    @property
    def groups(self) -> list:
        return groups(self.store, self.id)

    @property
    def permissions(self) -> list:
        return permissions(self.store, self.id)
