from dash_access.clients.base import BaseAccessStore
from dash_access.access.relationship import create, exists, delete, get_all, delete_all

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


class OperationPrincipal(object):
    """
    a principal that changes some operations
    a user or a group
    """

    def __init__(self, principal: str, principal_type: str):
        _checks(principal=principal, principal_type=principal_type)
        self.principal = principal
        self.principal_type = principal_type

    def delete(self, store: BaseAccessStore):
        return delete_all(
            store=store, principal=self.principal, principal_type=self.principal_type
        )

    def groups(self, store: BaseAccessStore):
        return get_all(
            store=store,
            principal=self.principal,
            principal_type=self.principal_type,
            granted_type="group",
        )

    def permissions(self, store: BaseAccessStore):
        return get_all(
            store=store,
            principal=self.principal,
            principal_type=self.principal_type,
            granted_type="permission",
        )


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

    def delete(self, store: BaseAccessStore):
        """
        delete all the relationships where this is granted to a principal
        """
        return delete_all(
            store=store, granted=self.granted, granted_type=self.granted_type
        )

    def groups(self, store: BaseAccessStore):
        return get_all(
            store=store,
            principal_type="group",
            granted=self.granted,
            granted_type=self.granted_type,
        )

    def users(self, store: BaseAccessStore):
        return get_all(
            store=store,
            principal_type=user,
            granted=self.granted,
            granted_type=self.granted_type,
        )


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
