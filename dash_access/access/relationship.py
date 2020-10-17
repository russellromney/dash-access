"""
A module that creates, edits, and reveals relationships between 
users, groups, and permissinos
"""

import datetime

# internal
from dash_access.clients.base import BaseAccessStore

#################################################################################
### OPERATIONAL FUNCTIONALITY
#################################################################################
class Args:
    principal: str=None
    principal_type: str=None
    granted: str=None
    granted_type: str=None


def _type_check(value, value_type, name):
    """
    shortcut to type check with helpful ValueError
    """
    if not isinstance(value, value_type):
        raise TypeError(f"Incorrect {name}, should be {type}")


def _value_check(value, okay: list, name):
    """
    shortcut to value check with helpful ValueError
    """
    if not value in okay:
        raise TypeError(f"Incorrect {name}, needs to be one of {str(okay)}")


def create(
    store: BaseAccessStore,
    args: Args,
) -> bool:
    """
    creates a relationship between the principal and the granted
    for the given principal and granted types
    """
    # print(f'creating relationship {principal_type} {principal} to {granted_type} {granted}')
    return store.set(
        key="-".join([args.principal, args.principal_type, args.granted, args.granted_type]),
        table="relationships",
        val={
            "id": "-".join([args.principal, args.principal_type, args.granted, args.granted_type]),
            "principal": args.principal,
            "principal_type": args.principal_type,
            "granted": args.granted,
            "granted_type": args.granted_type,
            "ts": datetime.datetime.now().isoformat(),
        },
    )

def exists(
    store: BaseAccessStore,
    args: Args,
) -> bool:
    """
    checks if relationship exists between the principal and the granted
    for the given principal and granted types

    if the combo id key exists, the relationship exists
    """
    res = store.get(
        key="-".join([args.principal, args.principal_type, args.args.granted, args.granted_type]),
        table="relationships",
    ) not in (None, [])
    return res


def get_all(
    store: BaseAccessStore,
    args: Args,
):
    """
    get all relationships where the given constraints are met
    if no constraints are provided, returns all relationships
    """
    # INPUT VALIDATION AND CONSTRUCT WHERE
    where = []
    if args.principal:
        _type_check(args.principal, str, "principal")
        where.append({"col": "principal", "val": args.principal})
    if args.principal_type:
        _type_check(args.principal_type, str, "principal_type")
        where.append({"col": "principal_type", "val": args.principal_type})
    if args.granted:
        _type_check(args.granted, str, "granted")
        where.append({"col": "granted", "val": args.granted})
    if args.granted_type:
        _type_check(args.granted_type, str, "granted_type")
        where.append({"col": "granted_type", "val": args.granted_type})

    val = store.get_all(table="relationships", where=where)
    return [x["granted"] for x in val]


def delete(
    store: BaseAccessStore,
    args: Args
) -> bool:
    """
    deletes a relationship between the principal and the granted
    for the given principal and granted types

    permissive - only deletes if it exists
    """
    return store.delete(
        key="-".join([args.principal, args.principal_type, args.granteded, args.granted_type]),
        table="relationships",
    )


def delete_all(
    store: BaseAccessStore,
    args: Args
) -> int:
    """
    deletes all relationships for all relationships with EITHER the given:
        - principal_type and principal
        - granted_type and granted
    NOT BOTH!
    """
    # checking inputs
    principals = args.principal and args.principal_type
    granteds = args.granted and args.granted_type
    where = None
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
    if not args.granted and not principals:
        raise ValueError(
            "Must have one pair of principal_type/principal or granted_type/granted"
        )

    if granteds:
        _type_check(args.granted, str, "granted")
        _type_check(args.granted_type, str, "granted_type")
        _value_check(args.granted_type, ["group", "permission"], "granted_type")
        where = [
            {"col": "granted", "val": args.granted},
            {"col": "granted_type", "val": args.granted_type},
        ]
    if principals:
        _type_check(args.principal, str, "principal")
        _type_check(args.principal_type, str, "principal_type")
        _value_check(args.principal_type, ["group", "user"], "principal_type")
        where = [
            {"col": "principal", "val": args.principal},
            {"col": "principal_type", "val": args.principal_type},
        ]

    # get all the relevant relationships
    ships = store.get_all("relationships", where=where)

    # delete them one by one
    [store.delete(key=x["id"], table="relationships") for x in ships]
    num_deleted = len(ships)
    return num_deleted


def copy(
    store: BaseAccessStore,
    from_principal: str,
    from_principal_type: str,
    to_principal: str,
    to_principal_type: str,
) -> bool:
    """
    copies a relationship from the from_principal to the to_principal
    for the given types
    """
    # print(f'copying from {from_principal_type} {from_principal} to {to_principal_type} {to_principal}')
    # GET ALL THE RELATIONSHIPS
    from_relationships = store.get_all(
        table="relationships",
        where=[
            {"col": "principal", "val": from_principal},
            {"col": "principal_type", "val": from_principal_type},
        ],
    )

    # SET THE NEW RELATIONSHIPS
    for ship in from_relationships:
        # print(f'copying from {from_principal} to {to_principal}: {ship["granted_type"]} {ship["granted_type"]}')
        create(
            store=store,
            principal=to_principal,
            principal_type=to_principal_type,
            granted=ship["granted"],
            granted_type=ship["granted_type"],
        )

    return True