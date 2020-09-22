# Development with Dash Access

The main goal of Dash Access is to enable a developer to easily and quickly build an interface of access-controlled permissions, keeping safety first and progression rate a close second.

First shortcuts: 
> TIP: use `utils.dev_utils.toast()` for quick, simple alerts that pop up in the top right with a success, failure, warning, info, etc. message based on Bootstrap "colors"

> TIP: use `utils.dev_utils.id_factory()` to create a unique `id('component-id')` function for each page that generates unique component IDs even with the same base `id`. This allows you to reuse *component and layout code* as well as function code for overlapping use cases. See examples of this in `system/pages/profile.py` sharing most code with `system/pages/admin_sections/edit_user.py`.

# Adding a page

Add the page in `pages/` and import in into `application.py`. Add it to the `router()` callback function.

# Creating access-controlled layouts

The critical code for permission control is `control.permission`. 
It checks whether the user is authenticated, if they have access to the permission.

You can specify an `alt` option for something to return if the access doesn't work. The default is `None`, which returns an empty string like `''` to the layout instead of the component. If `alt='div'`, it returns a div with `"Access Denied"`. This is mostly for demonstration as it is inelegant. I encourage you to customize the `alt` part of the `control.permission` function for your own needs. You can also specify `alt='bad'` which will redirect the user the `pages.bad.py` page, showing an access denied/bad page error.

> TIP: Don't include components in callbacks that might not appear on the page

> TIP: put access-controlled permissions inside of organization components like `dbc.Col` or `dbc.Row`. This allows the layout to not be affected by lack of access permissions.

An example: 

```python
from system import control

app.layout = html.Div(
    [
        control.permission(
            name='revenue-chart',
            alt='div',
            component=html.Div(
                "some important chart"
            )
        ),

        control.permission(
            name='data-for-most people',
            component=html.Div(
                'some graph that most people can see'
            )
        ),

        html.Div(
            [
                'some data for everyone',
                control.permission(
                    name='hidden-inside',
                    component='hidden data!'
                )
            ]
        )
    ]
)
```

The page shows three levels of access with the `control.permission` function. The first permission is more tightly controlled, with an permission name being checked. It shows an access denied error. The second is only controlled by an permission name, and doesn't show up if the user lacks permissions. The third is open to all, but it contains some access-controlled hidden data that doesn't show up if the user doesn't have access.

> TIP: only acces control a) an entire section, b) the actual component c) an entire page. Anything else is too complicated to reason about, or at least not worth the effort.

# Access-controlled data

Access to data permissions is controlled by a simple wrapper in `access.data.data_access`; an example is in `pages/home.py` in the "DATA FUNCTIONS" section:

```python
@data_access('thing1')
def get_thing1_data():
    # THIS PART ONLY RUNS IF THE USER HAS ACCESS
    return pd.DataFrame(dict(x=list(range(5)),y=list(range(5))))
```

The data permission's name is passed to the decorator, which checks the current user's permissions before allowing the function to run. If the user has access, the wrapper returns the function with any args and kwargs. If the user does not have access, the wrapper returns None, bypassing the function altogether. I encourage you to customize this wrapper to be more well-suited to your needs if it can be.

To recap: the developer is in charge of writing functions that know how to get each data source, with whatever parameters needed. Take note that:
- downstream consumers of the developer's function must know how to handle receiving `None` values
- the user must be granted explicit access to the permission or data permission with the exact passed-in name

> TIP: if a certain data permission is only used with a certain permission, give them the same name. Then you'll only have to grant access once.

# DB clients

Dash Access comes with custom clients to connect to a NoSQL type data store (prod and stage) or a traditional SQLite data store (dev). In the app and throughout the `access` code, the database used by various functions is passed by the `utils.dev_utils.store()` and `utils.dev_utils.logging_store()` helper functions. They check `os.environ` for the `APPLICATION_ENVIRONMENT` and return the correct store given the environment. Look there, and in `application.py` for how the database is setup. Currently it looks like:

```python
#####################################################
### SETUP APP DATABASE CONNECTIONS
#####################################################
@application.before_request
def before_request():
    # set the global db connections at app start
    env = os.environ['APPLICATION_ENVIRONMENT']
    if env == 'DEV':
        g.store = dev_utils.DevKeyValStore('./data/local.sqlite3')
        g.logging_store = dev_utils.DevLoggingStore('./data/local.sqlite3')
    elif env == 'STAGE':
        g.store = stage_clients.StageKeyValStore()
        g.logging_store = stage_clients.StageLoggingStore()
    elif env == 'PROD':
        g.store = clients.KeyValStore()
        g.logging_store = clients.LoggingStore()
```

### Features of all clients

- the `KeyValStore` class operates on the access tables
- the `LoggingStore` class operates on the logging tables
- pass values to the `KeyValStore` as a `key` and `dict` of field names mapped to values
- pass values to the `LoggingStore` as `**kwargs`
- the class' `__init__` method calls `self.instantiate()`
- you can overwrite `get_table()`, `instantiate()`, `table_key()`, `_insert()` etc. to inherit gracefully
- encoding and decoding are all the same; all inherit from `BaseClass` which encodes
- in `get`, always decode all `dict` values reading in
- in `set` or `insert`, always encode all `dict` values going to the database


### `utils.clients`: 

`BaseAccessStore`, the superclass; `KeyValStore` and `LoggingStore`, the prod classes; these all require a Flask app context to run, as they are passed the the `flask.g` global. These clients take care of encoding and decoding Python objects to database data. They run quite quickly in the cloud.

Key features:
- They turn lists and dicts into binary blobs, encoded by MessagePack
- They turn floats into `decimal.Decimals` (for Dynamo)
- They decode from Dynamo types like `decimal.Decimal` and `boto3.dynamodb.types.Binary`
- Use a single connection for each table, shared between app threads for max speed
- YOU CANNOT USE THEM OUTSIDE OF THE FLASK APP CONTEXT

### `utils.stage_clients`:

`StageKeyValStore` and `StageLoggingStore` are nearly identical to the prod variants, but they create a new `boto3` table connection every time a request is made. This means that they can be used for local development, but they are quite slow compared to being a) shared by threads b) in the cloud.

### `utils.dev_clients`:

`DevKeyValStore` and `DevLoggingStore` are wildly different from the prod variants, given that they use SQLite for storage instead of a local disk. The API is similar, however.

## Adding fields to a table

Table fields are used in many places. If you need to add a field, here are the places you'll need to 
add that field to:

| Location | Details | Table |
| --- | --- | --- |
| `utils.clients.BaseAccessStore` | a listing of all the fields in each table, for filling in missing values; THIS IS VERY IMPORTANT - IT FILLS IN ANY MISSING VALUES WITH A DEFAULT VALUE | all |
| `access.<table>.add()` | creates a dict of the user's data before adding; in `group`, `signup`, `user` | all |
| `utils.dev_env` | table creation functions for local development | all |
| `pages.admin_sections.signups` | admin approving signup | signups |
| `pages.signup` | signing up a new user; in layout and in callback | signups |
| `pages.admin_sections.add_group` | admin adding new group; in layout and in callback | groups |
| `pages.admin_sections.edit_group` | admin editing group; in layout and in callback | groups |
| `auth.user.User` | pulling all fields from user to store and make accessible through `flask_login.current_user` | users |
| `pages.admin_sections.add_user` | admin adding new user; in layout and in callback | users |
| `pages.admin_sections.edit_user` | admin editing user; in layout and in callback | users |
| `pages.profile` | allowing a user to see and edit their own information | users |



## Adding update/view functionality for a new field

### DB interfacing

Add the field to the `utils.clients.BaseAccessStore` in the `table_fields()` function so it gets filled in. Add it to the `utils.dev_env` in the create tables function (if you use it). 

Then, add it to the relevant `access.<table>` module. If it's a single field, add it to the `add()` function and create a `change_<field>()` function easily with the `dev_utils.field_change_factory()` helper function. If it's a list field, create your own functions to change/update the value. You don't need a custom `get` function, as you can just do `access.<table>.get(ID)[field]` for the same result and speed.

Once you have the new field in the table and working with the clients, you'll want to show it in the app and be able to change it in a predictable way. There is a system premade to make this easy(ier).

### Load

Each system page has a single function that loads all the values to the screen or, alternatively, clears them away. It's triggered by a load button. Look for that. Add your field to that function in the callback wrapper, in the `values` list, and in the outputs list.

### Update/Change

Next you might want to add the ability to change the new field in a safe way. **Safe** here means that if something goes wrong, the changes automatically roll back and return a failure.

There are two helper functions for safely changing/updating the fields in the database. Both handle the update and rollback for you after you define a simple update/rollback operation:

#### `utils.dev_utils.execute_change_operations()`

This is for *changing* the value of a single field that has a single value, e.g. name, or mobile. You pass it a list of dicts with commands called *operations* and a `change_name` and it handles the value change(s) for you. Here's an example from `edit_user.py`;  `record` is a user record:
```python
def do_change(...):
    ops = [
        {
            'ID': email,
            'done': True,
            'name': 'Mobile',
            'function': user.change_mobile,
            'new_value': mobile,
            'old_value': record['mobile'],
            'required': True,
            'validate': lambda x: phonenumbers.is_possible_number(record['country'])
        },
    ]
    return execute_change_operations(ops=ops, change_name='Mobile')
```

As you can see, you pass it the `ID` that will be used to make the change, a default `done` value, the operation name, the function that will make the change, the new_value, the rollback value, whether or not the value can be `None` or blank (i.e. required), and a function that validates the value by returning `True` or `False`.

The helper function makes the change and stops and rolls back if anything goes wrong.

#### `utils.dev_utils.execute_update_operations()`

This function is similar, except it manages *updates to list values*. You're adding or removing a(some) value(s) to/from a list, so there are two separate functions: one to make the change, and one to (separately) roll it back if something goes wrong - we can't just change the value to its old value and trust it will be the same.

This time, we remove the `old_value` and add a `rollback_function`. In this case, the validation function is acting on *each item in the value list*; if any fail, no changes are made and all associated changes are rolled back.

An example, also from `edit_user.py`, where `add` is a list of parsed data permissions:

```python
    ops = [
        {
            'ID': email,
            'done': True,
            'name': 'Add Data permissions',
            'function': user.add_permissions,
            'rollback_function': user.remove_permissions,
            'new_value': add,
            'required': False,
            'validate': lambda x: not x in ['',None]
        },
    ]
    return execute_update_operations(
        ops=ops,
        change_name=change_name
    )

```

# More

There are many more things that are useful to know in developing with Dash Access; most of the functions in the code have long docstrings (or readable code, I hope) that will help you understand how they work.