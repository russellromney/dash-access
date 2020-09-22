"""
A module that creates and reveals relationships between 
users and groups.
"""

import datetime

from dash_access.clients.base import BaseAccessStore


def create(
    store: BaseAccessStore,
    principal: str,
    principal_type: str,
    granted: str,
    granted_type: str,
) -> bool:
    """
    creates a relationship between the principal and the granted
    for the given principal and granted types
    """
    # print(f'creating relationship {principal_type} {principal} to {granted_type} {granted}')
    return store.set(
        key="-".join([principal, principal_type, granted, granted_type]),
        table="relationships",
        val={
            "id": "-".join([principal, principal_type, granted, granted_type]),
            "principal": principal,
            "principal_type": principal_type,
            "granted": granted,
            "granted_type": granted_type,
            "ts": datetime.datetime.now().isoformat(),
        },
    )


def helper_factory_create(principal_type: str, granted_type: str):
    """
    returns a helper function to create a relationship
    between a given principal with a certain principal type
    and a given granted with a certain granted type
    """

    def func(store: BaseAccessStore, principal: str, granted: str) -> list:
        f"""
        helper to create relationship between principal with type {principal_type}
        and granted of type {granted_type}
        """
        return create(
            store=store,
            principal=principal,
            principal_type=principal_type,
            granted=granted,
            granted_type=granted_type,
        )

    return func


user_group_create = helper_factory_create("user", "group")
user_permission_create = helper_factory_create("user", "permission")
group_group_create = helper_factory_create("group", "group")
group_permission_create = helper_factory_create("group", "permission")


def exists(
    store: BaseAccessStore,
    principal: str,
    principal_type: str,
    granted: str,
    granted_type: str,
) -> bool:
    """
    checks if relationship exists between the principal and the granted
    for the given principal and granted types

    if the combo id key exists, the relationship exists
    """
    res = (
        store.get(
            key="-".join([principal, principal_type, granted, granted_type]),
            table="relationships",
        )
        not in (None, [])
    )
    return res


def helper_factory_exists(principal_type: str, granted_type: str):
    """
    returns a helper function for a given principal-granted pairing
    """

    def func(store: BaseAccessStore, principal: str, granted: str) -> bool:
        f"""
        helper to check if {principal_type}-{granted_type} relationship exists
        """
        return exists(
            store=store,
            principal=principal,
            principal_type=principal_type,
            granted=granted,
            granted_type=granted_type,
        )

    return func


user_group_exists = helper_factory_exists("user", "group")
user_permission_exists = helper_factory_exists("user", "permission")
group_group_exists = helper_factory_exists("group", "group")
group_permission_exists = helper_factory_exists("group", "permission")


def helper_factory_all(principal_type: str, granted_type: str):
    """
    returns a helper function to get all relationships
    between a given principal with a certain principal type
    and all grants of type granted_type
    """

    def func(store: BaseAccessStore, principal: str) -> list:
        f"""
        helper to get all relationships between principal with type {principal_type}
        and grants of type {granted_type}
        """
        val = store.get_all(
            table="relationships",
            where=[
                {"col": "principal", "val": principal},
                {"col": "principal_type","val": principal_type},
                {"col": "granted_type", "val": granted_type},
            ],
        )
        return [x["granted"] for x in val]

    return func


user_group_all = helper_factory_all("user", "group")
user_permission_all = helper_factory_all("user", "permission")
group_group_all = helper_factory_all("group", "group")
group_permission_all = helper_factory_all("group", "permission")


def delete(
    store: BaseAccessStore,
    principal: str,
    principal_type: str,
    granted: str,
    granted_type: str,
) -> bool:
    """
    deletes a relationship between the principal and the granted
    for the given principal and granted types
    """
    return store.delete(
        key="-".join([principal, principal_type, granted, granted_type]),
        table="relationships",
    )


def helper_factory_delete(principal_type: str, granted_type: str):
    """
    returns a helper function to delete a relationship
    between a given principal with a certain principal type
    and a given granted with a certain granted type
    """

    def func(store: BaseAccessStore, principal: str, granted: str) -> list:
        f"""
        helper to create relationship between principal with type {principal_type}
        and granted of type {granted_type}
        """
        return delete(
            store=store,
            principal=principal,
            principal_type=principal_type,
            granted=granted,
            granted_type=granted_type,
        )

    return func


user_group_delete = helper_factory_delete("user", "group")
user_permission_delete = helper_factory_delete("user", "permission")
group_group_delete = helper_factory_delete("group", "group")
group_permission_delete = helper_factory_delete("group", "permission")


def delete_all(
    store: BaseAccessStore, name: str, col_type: str  # group | user
) -> bool:
    """
    deletes all relationships for a given entity name and type
    deletes relatinships as principal and as granted
    """
    # print(f'deleting all from {col_type} {name}')
    principals = store.get_all(
        "relationships",
        where=[
            {"col": "principal",  "val": name},
            {"col": "principal_type",  "val": col_type},
        ],
    )
    grants = store.get_all(
        "relationships",
        where=[
            {"col": "principal",  "val": name},
            {"col": "principal_type",  "val": col_type},
        ],
    )

    [store.delete(key=x["id"], table="relationships") for x in principals]

    [store.delete(key=x["id"], table="relationships") for x in grants]
    return True


def copy(
    store: BaseAccessStore, copy_from: str, from_type: str, copy_to: str, to_type: str,
) -> bool:
    """
    copies a relationship from the copy_from to the copy_to
    for the given types
    """
    # print(f'copying from {from_type} {copy_from} to {to_type} {copy_to}')
    # GET ALL THE RELATIONSHIPS
    from_relationships = store.get_all(
        table="relationships",
        where=[
            {"col": "principal",  "val": copy_from},
            {"col": "principal_type",  "val": from_type},
        ],
    )

    # SET THE NEW RELATIONSHIPS
    for ship in from_relationships:
        # print(f'copying from {copy_from} to {copy_to}: {ship["granted_type"]} {ship["granted_type"]}')
        create(
            store=store,
            principal=copy_to,
            principal_type=to_type,
            granted=ship["granted"],
            granted_type=ship["granted_type"],
        )

    return True


def helper_factory_copy(from_type: str, to_type: str):
    """
    returns a helper function to copy a relationship(s)
    from a given principal with a certain type
    to a given principal with a certain type
    """

    def func(store: BaseAccessStore, copy_from: str, copy_to: str) -> list:
        f"""
        helper to copy relationship between principals with type {from_type}
        and granted of type {to_type}
        """
        return copy(
            store=store,
            copy_from=copy_from,
            from_type=from_type,
            copy_to=copy_to,
            to_type=to_type,
        )

    return func


user_user_copy = helper_factory_copy("user", "user")
user_group_copy = helper_factory_copy("user", "group")
group_user_copy = helper_factory_copy("group", "user")
group_group_copy = helper_factory_copy("group", "group")

