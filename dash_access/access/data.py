import os
import datetime
import pandas
import json
from flask_login import current_user
from functools import wraps

# internal
from dash_access.access import user


def data_access(asset):
    """
    This wrapper manages access for access-controlled data retrieval functions.

    It checks if the logged-in user has access to the data asset;
        - if they do, return the function as normal
        - otherwise, it returns some value that your function should expect

    The principle is that each data asset has a custom function
    that knows how to pull the data only for that data asset.
    The system doesn't handle any of that, making it more flexible
    when data asset are not only from disk, or are in some
    structure that is not perfectly consistent.

    The system treats data assets like any other permission,
    i.e. access is granted and revoked to users and groups

    The custom function needs:
        - pass the asset name into the decorator at definition
        - should deal with the access failure value

    **Example**:
    from system import data_access
    @data_access('revenue')
    def get_revenue_data():
        '''returns a list of the revenue data'''
        some_field = current_user.some_field
        data = pd.read_csv(f'path/to/{some_field}/revenue.csv')
        return data
    """

    def decorated(f):
        def wrapper(*args, **kwargs):
            if not hasattr(current_user, "id"):
                # TODO add proper response
                return None

            # CHECK USER ACCESS RIGHTS
            has_access = current_user.has_access(current_user.id, asset)

            # RETURN IF USER DOES NOT HAVE ACCESS
            if not has_access:
                return None

            # RETURN FUNCTION AS NORMAL OTHERWISE
            else:
                return f(*args, **kwargs)

        return wrapper

    return decorated
