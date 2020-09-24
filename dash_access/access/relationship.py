"""
A module that creates, edits, and reveals relationships between 
users and groups.
"""

import datetime

from dash_access.clients.base import BaseAccessStore

#################################################################################
### OPERATIONAL FUNCTIONALITY
#################################################################################
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
    res = store.get(
        key="-".join([principal, principal_type, granted, granted_type]),
        table="relationships",
    ) not in (None, [])
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


def get_all(
    store: BaseAccessStore,
    principal: str = None,
    principal_type: str = None,
    granted: str = None,
    granted_type: str = None,
):
    """
    get all relationships where the given constraints are met
    if no constraints are provided, returns all relationships
    """
    # INPUT VALIDATION AND CONSTRUCT WHERE
    where = []
    if principal:
        _type_check(principal, str, "principal")
        where.append({"col": "principal", "val": principal})
    if principal_type:
        _type_check(principal_type, str, "principal_type")
        where.append({"col": "principal_type", "val": principal_type})
    if granted:
        _type_check(granted, str, "granted")
        where.append({"col": "granted", "val": granted})
    if granted_type:
        _type_check(granted_type, str, "granted_type")
        where.append({"col": "granted_type", "val": granted_type})

    val = store.get_all(table="relationships", where=where)
    return [x["granted"] for x in val]


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
        return get_all(
            store=store,
            principal=principal,
            principal_type=principal_type,
            granted_type=granted_type,
        )

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

    permissive - only deletes if it exists
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
    store: BaseAccessStore,
    principal: str = None,
    principal_type: str = None,
    granted: str = None,
    granted_type: str = None,
) -> int:
    """
    deletes all relationships for all relationships with EITHER the given:
        - principal_type and principal
        - granted_type and granted
    NOT BOTH!
    """
    # checking inputs
    principals = principal and principal_type
    granteds = granted and granted_type
    if principals:
        if granteds:
            raise ValueError(
                "Only one pair of principal_type/principal or granted_type/granted is allowed"
            )
    if granteds:
        if principals:
            raise ValueError(
                "Only one pair of principal_type/principal or granted_type/granted is allowed"
            )
    if not granted and not principals:
        raise ValueError(
            "Must have one pair of principal_type/principal or granted_type/granted"
        )

    if granteds:
        _type_check(granted, str, "granted")
        _type_check(granted_type, str, "granted_type")
        _value_check(granted_type, ["group", "permission"], "granted_type")
        where = [
            {"col": "granted", "val": granted},
            {"col": "granted_type", "val": granted_type},
        ]
    if principals:
        _type_check(principal, str, "principal")
        _type_check(principal_type, str, "principal_type")
        _value_check(principal_type, ["group", "user"], "principal_type")
        where = [
            {"col": "principal", "val": principal},
            {"col": "principal_type", "val": principal_type},
        ]

    # get all the relevant relationships
    ships = store.get_all("relationships", where=where)

    # delete them one by one
    [store.delete(key=x["id"], table="relationships") for x in ships]
    num_deleted = len(ships)
    return num_deleted


def copy(
    store: BaseAccessStore, copy_from: str, from_type: str, copy_to: str, to_type: str
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
            {"col": "principal", "val": copy_from},
            {"col": "principal_type", "val": from_type},
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