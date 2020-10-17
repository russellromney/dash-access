# dash-access

This package enables simple, granular user access management within Dash, with built-in 
event logging and integration with Flask-Login.

Add the `AccessUserMixin` to your `flask_login` `User` class:

```python
from flask_login import UserMixin
from dash_access import AccessUserMixin, PostgresAccessStore
from flask_sqlalchemy import SQLAlchemy

class User(UserMixin, db.Model, AccessUserMixin):
    __tablename__ = "users"
    __access_store__ = PostgresAccessStore(POSTGRES_URI)
    ...
```

Control user access within your layout with `dash_access.Controlled`:

```python
from dash_access import Controlled

app.layout = html.Div([
    Controlled(
        name="level1",
        alt="div",
        component = html.H1("Some controlled value"),
    ),
])
```

This checks the `current_user`'s permissions; if the user has access to the given permission name,
the component is returned as planned; otherwise, the `alt` option is returned. `alt` has three options:
- blank: return `""` (most common)
- `"div"`: return an `html.Div` that says `"Access Denied"`
- `"bad"`: return a link that sends the user to your /bad URL (customizable - useful for full-page control)
- `"custom"`: return a custom value defined in the `custom_value` parameter

dash-access comes with an administration API to create and manage access relationships. 
Custom database connectors are provided for PostgresQL, SQLite3, MySQL, DynamoDB, and SQLAlchemy.

Included in `/examples` are apps that demonstrate full functionality and potential administration workflows.

# securing a Dash app

**Authentication** is the first step: making sure each user has logged in before showing 
them any content. 

**Authorization** is next: the user must be *authorized* to perform
some action or to see some content. "Authentication" and "authorization"
sound too similar, so dash-access uses the term **access control**.

## key ideas

dash-access has six main concepts:
- **principal**: an entity (user, group) 
- **permission**: allows some **principal** to access some controlled asset
- **group**: a named collection of **permissions**
- **grant**: the action of giving a principal access to a permission
- **relationship**: the stored link between the principal and the granted permission
- **inherits**: a group can be *granted* another group, thus *inheriting* its permissions

### group inheritance

Group permission inheritance allows groups to fullfill the policy, role, and 
group functions of [traditional RBAC](https://auth0.com/docs/authorization/rbac).
Most access control problems in Dash are simple and most applications are relatively small
so adding the additional levels of policy and role make reasoning more complex rather than 
more useful.

A common pattern is granting permissions to a group and 
granting that group to another group to create tiers of access among users.

### permission blindness

In dash-access, a permission is **blind**: it doesn't exist outside of 
being granted to a group or user. A permission does not need to be 
registered or saved anywhere - it is just a string name.

In the example, `level1` and `level2` are arbitrary permission names. 
`level1` has been granted to the user `test`, but `level2` has 
not been granted, so anything requiring `level2` will not be shown to user `test`.

Relationships are the secret sauce of `dash_access`: each permission is defined
as a relationship where a principal is granted a permission of some kind. A user-permission
relationship allows a user to access some asset that requires that permission. A user-group
relationship gives a user access to the groups's permissions. A group-group relationship extends
one group's permissions to encompass another group's permissions.

You can access this system in two ways: by adding an access store and access user mixin to your 
`User` class model a la `flask_login`, or directly by calling the `dash_access`
internal functions. The first option covers most use cases with Dash, but the latter is more flexible.

Control user access within your layout with `dash_access.Controlled`. This looks like

```python
Controlled(
    name="level1",
    alt="div",
    component = html.H1("Some controlled value"),
)
```

This checks the current user's permissions; if the user has access to the given permission name,
the component is returned as planned; otherwise, the `alt` option is returned. `alt` has three options:
- blank: return `""`
- `"div"`: return an `html.Div` that says `"Access Denied"`
- `"bad"`: return a link that changes the page to your `/bad` page link (custom)

# Internals

dash-access internals are exposed through `dash_access.access`. Each function gets passed an access database and some parameters to create some access control operation. The following is not an exhaustive list:

```python
The relationship API is how you access direct relationships.
```

```python
import dash_access as da
store = da.Sqlite3AccessStore("local.sqlite3")

# basic API
from dash_access import relationship as rship
rship.create(store, rship.Args(principal="me",principal_type="user",granted="powers",granted_type="permission"))
rship.exists(store,rship.Args("me","user","powers","permission"))
rship.delete(store,rship.Args("me","user","powers","permission"))
rship.copy(store,from_principal="me",from_principal_type="user",to_principal="them",to_principal_type"user")
rship.get_all(store,rship.Args("me","user",granted_type="group"))
```

# DB Clients

Custom database connectors are provided for PostgreSQL, SQLite3, MySQL, DynamoDB, and SQLAlchemy.

**Why pass around a custom `store` everywhere?**

At first it seems strange to pass a `store` object to each function. 
However, this is an intentional decision with practical benefits:
- access management is not connected the Flask app context
- you can use the API in a Jupyter notebook without an app running
- you can use a different `store` type in different environments - for example, SQLite3 for local development and PostgreSQL for staging and production envs
- custom `where` statements for flexible queries, handled in a different way by each client type


# Logging

Two event types are logged by default: admin events and access events

### admin_events

Any operation that creates, updates, or deletes an access relationship or group logs an event to the `admin_events` table. 

### access_events

Whenever a user attempts to access a permission, the attempt is logged in the `access_events` table.

These two event logs make it easy to see who tried to access a permission, when they tried to access it, and what the outcome was.

# Example

First, install dash_access:

```sh
pip install dash-access
```

Then set up the app and create the databases it will use for authentication and access control:

```python
# server.py
from dash_access import Sqlite3AccessStore, AccessUserMixin
from flask_login import UserMixin, LoginManager

app = dash.Dash(__name__)
db = SQLAlchemy() # in-memory sqlite
login_manager = LoginManager(app)

# create the User model
class User(UserMixin, db.Model, AccessUserMixin):
    __tablename__ = "users"
    __access_store__ = Sqlite3AccessStore("local.db") # on-disk sqlite

    id = db.Column(db.String(40), primary_key=True)
    password = db.Column(db.String(200), nullable=False, unique=False)

    def set_password(self, password):
        """Create hashed password."""
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """Check hashed password."""
        return check_password_hash(self.password, password)

    @classmethod
    def get(self, user_id: str):
        return User.query.filter_by(id=user_id).first()

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# run once before starting the app
if __name__=="__main__":
    with app.app_context():
        db.create_all()
        
        test = User(id='test',name='test',)
        test.set_password("test")
        test.add_permission("level1")
        db.session.add(test)
        db.session.commit()
```

Create the initial database tables once with:

```sh
python server.py
```

Finally, create the access-controlled app that uses the previously-created database:

```python
# app.py
import dash
import dash_html_components as html
from dash_access import Controlled
from server import app

def login_layout():
    return [
        dbc.Input(id='username',placeholder='username'),
        dbc.Input(id='password',placeholder='password'),
        dbc.Button("login",id='login'),
    ]

app.layout = html.Div([
    dcc.Location(id="url",refresh=False),
    html.Div(id='content'),
])

def home():
    return html.Div([
        html.H1("Accessible to all"),
        Controlled("level1","div",html.H1("Need level1 access")),
        Controlled("level2","div",html.H1("Need level2 access")),
    ])

@app.callback(Output("url","pathname"),[Input("login","n_clicks")],[State("username","value"),State("password","value")])
def login(n_clicks, email, pw):
    existing_user = User.get(email)
    if existing_user:
        if existing_user.check_password(pw):
            login_user(existing_user)
        return "/home"
    return dash.no_update

@app.callback(Output("content","children"),[Input("url","pathname")])
def router(url):
    if url=="/home" or url=='/':
        if current_user.is_authenticated:
            return home()
    if url=='/login':
        if current_user.is_authenticated:
            return home()
    return login()

if __name__ == "__main__":
    app.run_server(debug=True,port=8050)

```

and run it with

```sh
python app.py
```
