"""
A module that creates, edits, and reveals relationships with an object-oriented API
"""

from dash_access.clients.base import BaseAccessStore
from dash_access.access.relationship import create, exists, delete, get_all, delete_all, copy

#################################################################################
### API OBJECTS
#################################################################################
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


def _checks(
    principal: str = None,
    principal_type: str = None,
    granted: str = None,
    granted_type: str = None,
):
    if principal:
        _type_check(principal, str, "principal")
    if principal_type:
        _type_check(principal_type, str, "principal_type")
        _value_check(principal_type, ["group", "user"], "principal_type")
    if granted:
        _type_check(granted, str, "granted")
    if granted_type:
        _type_check(granted_type, str, "granted_type")
        _value_check(granted_type, ["group", "permission"], "granted_type")


class OperationPrincipalGet(object):
    """
    passthrough for getting some type of relationships for the principal
    """

    def __init__(self, principal: str, principal_type: str):
        _checks(principal=principal, principal_type=principal_type)
        self.principal = principal
        self.principal_type = principal_type

    def all(self, store: BaseAccessStore) -> list:
        """get all direct relationships where this is the principal"""
        return get_all(
            store=store,
            principal=self.principal,
            principal_type=self.principal_type,
        )

    def groups(self, store: BaseAccessStore) -> list:
        """get all direct relationships with groups where this is the principal"""
        return get_all(
            store=store,
            principal=self.principal,
            principal_type=self.principal_type,
            granted_type="group",
        )

    def permissions(self, store: BaseAccessStore) -> list:
        """get all direct relationships with permissions where this is the principal"""
        return get_all(
            store=store,
            principal=self.principal,
            principal_type=self.principal_type,
            granted_type="permission",
        )


class OperationPrincipalDelete(object):
    """
    passthrough for deleting some type of relationships for the principal
    """

    def __init__(self, principal: str, principal_type: str):
        _checks(principal=principal, principal_type=principal_type)
        self.principal = principal
        self.principal_type = principal_type

    def all(self, store: BaseAccessStore):
        """delete all relationships where this is the principal"""
        return delete_all(
            store=store,
            principal=self.principal,
            principal_type=self.principal_type,
        )

    def groups(self, store: BaseAccessStore):
        """delete all relationships where this principal is granted a group"""
        return delete_all(
            store=store,
            principal=self.principal,
            principal_type=self.principal_type,
            granted_type="group",
        )

    def permissions(self, store: BaseAccessStore):
        """delete all relationships where this principal is granted a permission"""
        return delete_all(
            store=store,
            principal=self.principal,
            principal_type=self.principal_type,
            granted_type="permission",
        )


class OperationPrincipalCopy(object):
    """
    passthrough for getting some type of relationships for the principal
    """

    def __init__(self, principal: str, principal_type: str):
        _checks(principal=principal, principal_type=principal_type)
        self.principal = principal
        self.principal_type = principal_type

    def group(self, store: BaseAccessStore, principal: str) -> list:
        """copy this principal's relationships to a group"""
        return copy(
            store=store,
            from_principal=self.principal,
            from_principal_type=self.principal_type,
            to_principal=principal,
            to_principal_type="group",
        )

    def user(self, store: BaseAccessStore, principal: str) -> list:
        """copy this principal's relationships to a user"""
        return copy(
            store=store,
            from_principal=self.principal,
            from_principal_type=self.principal_type,
            to_principal=principal,
            to_principal_type="user",
        )


class OperationPrincipal(object):
    """
    a principal that changes some operations
    a user or a group
    """

    def __init__(self, principal: str, principal_type: str):
        _checks(principal=principal, principal_type=principal_type)
        self.principal = principal
        self.principal_type = principal_type

    @property
    def delete(self):
        return OperationPrincipalDelete(self.principal, self.principal_type)

    @property
    def get(self):
        return OperationPrincipalGet(self.principal, self.principal_type)


class Principal(object):
    """
    passthrough for intuitive relationship operations on operations on principals
    can be a user or a group
    """

    def __init__(self, principal_type: str):
        _checks(principal_type=principal_type)
        self.principal_type = principal_type

    @classmethod
    def group(cls, principal: str):
        return OperationPrincipal(principal, "group")

    @classmethod
    def user(cls, principal: str):
        return OperationPrincipal(principal, "user")


class Grant(object):
    """
    passthrough for intuitive relationship operations on grants
    """

    @classmethod
    def group(cls, granted: str):
        return Granted(granted=granted, granted_type="group")

    @classmethod
    def permission(cls, granted: str):
        return Granted(granted=granted, granted_type="permission")


class GrantedGet(object):
    """
    passthrough for getting some type of relationships for the granted
    """

    def __init__(self, granted: str, granted_type: str):
        _checks(granted=granted, granted_type=granted_type)
        self.granted = granted
        self.granted_type = granted_type

    def all(self, store: BaseAccessStore) -> list:
        """get all direct relationships where this is the granted"""
        return get_all(
            store=store,
            granted=self.granted,
            granted_type=self.granted_type,
        )

    def users(self, store: BaseAccessStore) -> list:
        """get all direct relationships with groups where this is the granted"""
        return get_all(
            store=store,
            granted=self.granted,
            granted_type=self.granted_type,
            principal_type="user",
        )

    def groups(self, store: BaseAccessStore) -> list:
        """get all direct relationships with permissions where this is the granted"""
        return get_all(
            store=store,
            granted=self.granted,
            granted_type=self.granted_type,
            principal_type="group",
        )


class GrantedDelete(object):
    """
    passthrough for deleting some type of relationships for the granted
    """

    def __init__(self, granted: str, granted_type: str):
        _checks(granted=granted, granted_type=granted_type)
        self.granted = granted
        self.granted_type = granted_type

    def all(self, store: BaseAccessStore):
        """delete all relationships where this is the granted"""
        return delete_all(
            store=store,
            granted=self.granted,
            granted_type=self.granted_type,
        )

    def users(self, store: BaseAccessStore):
        """delete all relationships where this granted is granted to a user"""
        return delete_all(
            store=store,
            granted=self.granted,
            granted_type=self.granted_type,
            principal_type="user",
        )

    def groups(self, store: BaseAccessStore):
        """delete all relationships where this granted is granted to a group"""
        return delete_all(
            store=store,
            granted=self.granted,
            granted_type=self.granted_type,
            principal_type="group",
        )


class Granted(object):
    """
    something that is being granted to a principal
    can be a group or a permission

    errors:
        ValueError
    """

    def __init__(self, granted: str, granted_type: str):
        _checks(granted=granted, granted_type=granted_type)
        self.granted = granted
        self.granted_type = granted_type

    @property
    def to(self):
        return GrantTo(granted=self.granted, granted_type=self.granted_type)

    @property
    def delete(self):
        return OperationPrincipalDelete(self.principal, self.principal_type)

    @property
    def get(self):
        return OperationPrincipalGet(self.principal, self.principal_type)


class GrantPrincipal(object):
    """
    a principal that is being granted something
    """

    def __init__(
        self, principal: str, principal_type: str, granted: str, granted_type: str
    ):
        _checks(
            principal=principal,
            principal_type=principal_type,
            granted=granted,
            granted_type=granted_type,
        )
        self.principal = principal
        self.principal_type = principal_type
        self.granted = granted
        self.granted_type = granted_type

    def exists(self, store: BaseAccessStore):
        return exists(
            store=store,
            principal=self.principal,
            principal_type=self.principal_type,
            granted=self.granted,
            granted_type=self.granted_type,
        )

    def delete(self, store: BaseAccessStore):
        return delete(
            store=store,
            principal=self.principal,
            principal_type=self.principal_type,
            granted=self.granted,
            granted_type=self.granted_type,
        )

    def create(self, store: BaseAccessStore):
        return create(
            store=store,
            principal=self.principal,
            principal_type=self.principal_type,
            granted=self.granted,
            granted_type=self.granted_type,
        )

    def create(self, store: BaseAccessStore):
        return create(
            store=store,
            principal=self.principal,
            principal_type=self.principal_type,
            granted=self.granted,
            granted_type=self.granted_type,
        )


class GrantTo(object):
    """
    passthrough for intuitive relationship operations on granting
    """

    def __init__(self, granted: str, granted_type: str):
        _checks(granted=granted, granted_type=granted_type)
        self.granted = granted
        self.granted_type = granted_type

    def group(self, principal: str):
        return GrantPrincipal(
            principal=principal,
            principal_type="group",
            granted=self.granted,
            granted_type=self.granted_type,
        )

    def user(self, principal: str):
        return GrantPrincipal(
            principal=principal,
            principal_type="user",
            granted=self.granted,
            granted_type=self.granted_type,
        )
