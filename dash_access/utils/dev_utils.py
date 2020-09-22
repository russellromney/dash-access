from flask import g
import os
from dotenv import load_dotenv

from clients import sqlite3
import dash_bootstrap_components as dbc

def field_change_factory(field: str, put=None, get=None, hint=None):
    """
    Helper function to create change functions
    This is only really useful for Dynamo or other key/val stores where you need to grab the entire record to change it
        ...unlike update function with SQL engines or hash updates with Redis

    field, str
        is the actual field name to change in the record
    put, function
        is the function to put a db record to the db for record with unique _ID. Should return True/False
        takes in a unique ID and record and updates the record matching that ID in DB
        returns True if success, False if fails (including record not exist)
    get, function
        is the function to get a db record from the db with unique _ID
        takes in unique ID and returns a dict record matching that ID, or None
        Should return None if no record available.
    hint, type
        is the type hint used for the function (or None)
        if None, no hint is used
    
    returns a function that changes the record as specified
    """
    # PUTFUNC CANNOT BE NONE
    if put is None:
        raise ValueError('dev_utils.field_change_factory: arg "put" must be a put function like get(ID: str, record: dict)')
    if get is None:
        raise ValueError('dev_utils.field_change_factory: arg "get" must be a get function like get(ID: str)')
    
    # NO TYPE HINT
    if hint is None:
        def func(_ID: str, value):
            record = get(_ID)
            if not record:
                return False
            record[field] = value
            res = put(_ID, record)
            return res
        return func
    
    # WITH TYPE HINT
    else:
        def func(_ID: str, value: hint):
            record = get(_ID)
            if not record:
                return False
            record[field] = value
            res = put(_ID, record)
            return res
        return func


def id_factory(page: str):
    def func(_id: str):
        """
        Dash pages require each component in the app to have a totally
        unique id for callbacks. This is easy for small apps, but harder for larger 
        apps where there is overlapping functionality on each page. 
        For example, each page might have a div that acts as a trigger for reloading;
        instead of typing "page1-trigger" every time, this function allows you to 
        just use id('trigger') on every page.
        
        How:
            prepends the page to every id passed to it
        Why:
            saves some typing and lowers mental effort

        **Example**
        # SETUP
        from utils.utils import id_factory
        id = id_factory('page1') # create the id function for that page
        
        # LAYOUT
        layout = html.Div(
            id=id('main-div')
        )

        # CALLBACKS
        @app.callback(
            Output(id('main-div'),'children'),
            Input(id('main-div'),'style')
        )
        def funct(this):
            ...
        """
        return f"{page}-{_id}"
    return func



def toast(chil: str, success):
    """
    a quick toast thing for success or failure
    success:
        True -> 'success'
        False -> 'danger'
        'info' -> 'info'
        'warning' -> 'warning'
    """
    if success in ('success',True):
        header = 'Success'
        icon = 'success'
    elif success == 'warning':
        header = 'Warning'
        icon = 'warning'
    elif success in (False, 'danger'):
        header = 'Failure'
        icon = 'danger'
    elif success == 'info':
        header = 'Info'
        icon = 'info'
    else:
        header = 'Warning',
        icon = 'warning'
    return dbc.Toast(
        chil,
        header=header,
        is_open=True,
        icon=icon,
        duration=4000,
        style={"position": "fixed", "top": "8%", "right": "1%", "width": "25%", "z":5000},
    )


#########################################################################
# HELPER FUNCTION TO MAKE ALL CHANGES SAFELY WITH ROLLBACKS - TO VALUES
#########################################################################
def execute_change_operations(ops: list, change_name: str):
    """
    This function loops through a list of these operations and attempts to make the change.
    If one change fails or the new value is invalid, rolls back all changes.

    An "op" i.e. "operation" looks like:
        {
            'ID': name
            'done': True,
            'name': 'Phone',
            'function': user.change_phone,
            'rollback_function': user.change_phone,
            'new_value': phone,
            'old_value': record['phone'],          
            'required': True,
            'validate': lambda x: phonenumbers.is_possible_number(phonenumbers.parse(phone, pycountry.countries.lookup(record['country']).alpha_2))
        }

    NOTE: 
        - all keys must exist for it to work
        - validate must return True or False
        - validate must be a function
        - change_name describes the values being changed; e.g. for changes to phone/mobile, use "Phone/Mobile"
        - doesn't allow None or empty string if 'required' = True
    
    ROLLBACK FUNCTION
        - an optional field that uses a different function to rollback the changes
        - function and rollback_function can be the same
        - rollback function is not required
        - if specified, the rollback function is used to revert the change
        - the rollback function uses the NEW value, instead of changing back to the old value

    ORDER OF OPERATIONS
        - check that new values are not empty or None (if required); stop if so
        - check that all values are not totally the same; stop if so
        - run the operations for each one that is different from the old value
            * validate the value using the "validate" function
            * if valid, make the change
            * else, stop everything and send a notif of invalid value back to the user
        - if all the changes worked, send a success reply
        - else, rollback all changes and send either
            * the thing that triggered the rollbacks (if exists)
            * a general failure message
    
    Returns a utils.toast() (dbc.Toast wrapper) with feedback info.
    """
    bad = ['',None]

    for op in ops:
        if op['new_value']:
            op['new_value'] = op['new_value'].strip()
        
        # CHECK BLANK IF REQUIRED
        if op['required']:
            if op['new_value'] in bad:
                return toast(f'{op["name"]} cannot be blank.','danger')

    # CHECK ALL VALUES ARE SAME
    if all([op['new_value'] == op['old_value'] for op in ops]):
        return toast('Values are the same.','warning')

    # DO THE CHANGES IF THE VALUES ARE DIFFERENT
    rollbacks = False
    for op in ops:
        if not op['new_value'] == op['old_value']:        
            # VALIDATE THE NEW VALUE
            # if invalid, we'll rollback all and stop all
            try:
                if not op['validate'](op['new_value']):
                    rollbacks = op['name']
                    break
            except:
                rollbacks = op['name']
                break
                
            op['done'] = op['function'](op['ID'], op['new_value'])

    # IF ALL GOOD, SEND IT        
    if not rollbacks and all([op['done'] for op in ops]):
        return toast(f'Successfully changed {change_name}','success')
    
    # ELSE, ROLLBACK
    else:
        for op in ops:
            # USE ROLLBACK FUNCTION IF SPECIFIED
            if 'rollback_function' in op:
                op['rollback_function'](op['ID'], op['new_value'])
            else:
                op['function'](op['ID'], op['old_value'])
        
        # INVALID VALUE MESSAGE
        if rollbacks:
            return toast(f'{rollbacks} is not valid.','danger')

        # ROLLBACK MESSAGE
        return toast(f'Unable to change {change_name}. Rolled back.','failure')


#########################################################################
# HELPER FUNCTION TO MAKE ALL CHANGES SAFELY WITH ROLLBACKS - TO LISTS
#########################################################################
def execute_update_operations(ops: list, change_name: str):
    """
    This function loops through a list of these operations and attempts to update the value list
    If one change fails or the new value is invalid, rolls back all changes.

    This is different from the value-only function in that it updates lists.
    This means that you use a different function to add to a list than to remove from it.
    It also means that the values cannot be compared before after.
    Key differences:
        - "rollback_function" field
        - no "old_value" field
        - new_value is a list
        - validation is run on each item of the list provided in new_value

    An "op" i.e. "operation" looks like:
        {
            'ID': email,
            'done': True,
            'name': 'Phone',
            'function': user.change_phone,
            'rollback_function': user.change_phone,
            'new_value': phone,
            'required': True,
            'validate': lambda x: phonenumbers.is_possible_number(phonenumbers.parse(phone, pycountry.countries.lookup(record['country']).alpha_2))
        }

    NOTE: 
        - all keys must exist for it to work
        - "validate" must return True or False
        - "validate" must be a function
        - change_name describes the values being changed; e.g. for changes to phone/mobile, use "Phone/Mobile"
        - doesn't allow "new_value" to be None or empty string if 'required' = True
    
    ROLLBACK FUNCTION 
        - uses a different function to rollback the changes
        - function and rollback_function can be the same
        - rollback function is not required
        - if specified, the rollback function is used to revert the change
        - the rollback function uses the NEW value, instead of changing back to the old value

    ORDER OF OPERATIONS
        - check that new values are not empty or None (if required); stop if so
        - run the operations for each one that is different from the old value
            * validate the value using the "validate" function
            * if valid, make the change
            * else, stop everything and send a notif of invalid value back to the user
        - if all the changes worked, send a success reply
        - else, rollback all changes and send either
            * a message containing the thing that triggered the rollbacks (if exists)
            * a general failure message
    
    Returns a utils.toast() (dbc.Toast wrapper) with feedback info.
    """
    for op in ops:        
        # CHECK BLANK IF REQUIRED
        if op['required']:
            if op['new_value'] == []:
                return toast(f'{op["name"]} cannot be blank.','danger')

    # DO THE CHANGES (DOES NOTHING IF THE LIST OF ADDS/REMOVES IS EMPTY)
    rollbacks = False
    for op in ops:
        # VALIDATE THE NEW VALUE
        # if invalidm stop the whole thing and rollback everything
        if not all([ op['validate'](val) for val in op['new_value']]):
            rollbacks = op['name']
            break
        op['done'] = op['function'](op['ID'], op['new_value'])

    # IF ALL GOOD, SEND IT
    if not rollbacks and all([op['done'] for op in ops]):
        return toast(f'Success: {change_name}','success')
    
    # ELSE, ROLLBACK
    else:
        for op in ops:
            # USE ROLLBACK FUNCTION IF SPECIFIED
            op['rollback_function'](op['ID'], op['new_value'])
        
        # INVALID VALUE MESSAGE (IF THAT'S WHY IT STOPPED)
        if rollbacks:
            return toast(f'{rollbacks} value is not valid.','danger')

        # FAILURE ROLLBACK MESSAGE (UNKNOWN FAILURE?)
        return toast(f'Unsuccessful: {change_name}. Rolled back.','failure')