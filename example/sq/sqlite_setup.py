# external imports
import dash
import dash_bootstrap_components as dbc
from dash_access import generate_password_hash, check_password_hash, AccessUserMixin, Sqlite3AccessStore
from dash_access.clients.sqlite3 import create_tables, drop_tables
from dash_access.access import group

import sqlite3
from flask_login import UserMixin, LoginManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
login_manager = LoginManager()


class User(UserMixin, AccessUserMixin, db.Model):
    """
    representation of a user for this example program
    """

    __tablename__ = "flasklogin-users"
    __access_store__ = Sqlite3AccessStore("local.sqlite3")

    def __repr__(self):
        return "<User {}>".format(self.id)

    id = db.Column(db.String(40), primary_key=True)
    password = db.Column(db.String(200), nullable=False, unique=False)
    name = db.Column(db.String(100), nullable=False, unique=False)

    def set_password(self, password):
        """Create hashed password."""
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """Check hashed password."""
        return check_password_hash(self.password, password)

    @classmethod
    def get(self, user_id: str):
        return User.query.filter_by(id=user_id).first()



app = dash.Dash(__name__,external_stylesheets=[dbc.themes.BOOTSTRAP],prevent_initial_callbacks=True)
app.config.suppress_callback_exceptions = True

server = app.server
server.secret_key = 'my secret key'
login_manager.init_app(server)
db.init_app(server)

with server.app_context():
    db.create_all()
    
    sq = Sqlite3AccessStore(path='local.sqlite3')
    sq.drop_tables()
    sq.create_tables()

    # create groups structure
    group.add(sq, name="all",permissions=["*"])
    group.add(sq, name="entry",permissions=["open"])
    group.add(sq, name="mid",permissions=["sensitive"],inherits=["entry"])
    group.add(sq, name="top",permissions=["classified"],inherits=["mid"])
    
    
    admin = User(id='admin',name='admin')
    admin.set_password("test")
    admin.add_group("all")
    
    employee = User(id='employee',name='employee')
    employee.set_password("test")
    employee.add_group("entry")
    
    manager = User(id='manager',name='manager')
    manager.set_password("test")
    manager.add_group("mid")
    
    executive = User(id='executive',name='executive')
    executive.set_password("test")
    executive.add_group("top")
    
    db.session.add(admin)
    db.session.add(employee)
    db.session.add(manager)
    db.session.add(executive)
    db.session.commit()

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)
