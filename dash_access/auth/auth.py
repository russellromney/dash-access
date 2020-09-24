# external imports
from functools import wraps
from flask_login import current_user, AnonymousUserMixin
import datetime
import decimal

# local imports
from utils.utils import html, dcc, dbc
from auth.pw import check_password_hash
from access import user
from auth.user import User


def attempt_user_login(user_id: str = None, password: str = None):
    """
    Attempt to authenticate a user and log the attempt and outcome

    returns False if
        the user does not exist
        OR
        the user's password is incorrect
    return True if
        the user exists
        AND
        the user's password is correct

    At the end, log the login attempt and return the outcome and
    an instance of User representing the user_id (or None)
    """
    reason = None
    correct_password = False

    if user_id is None or password is None:
        # no need to log login attempt - missing stuff
        return False

    elif not user.exists(user_id):
        reason = "user does not exist"
        me = AnonymousUserMixin()
        me.id = user_id
    else:
        me = User(user_id)

        correct_password = check_password_hash(me.password, password)
        if not correct_password:
            reason = "incorrect password"

    # LOG LOGIN ATTEMPT
    user.login_attempt(
        email=me.id,
        action="login",
        ts=decimal.Decimal(datetime.datetime.now().timestamp()),
        status=correct_password,
        reason=reason,
    )

    return correct_password, me
