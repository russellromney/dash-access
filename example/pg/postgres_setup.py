# external imports
import dash
import dash_bootstrap_components as dbc
from dash_access import (
    generate_password_hash,
    check_password_hash,
    AccessUserMixin,
    PostgresAccessStore,
)
from dash_access.access import group

from flask_login import UserMixin, LoginManager
from flask_sqlalchemy import SQLAlchemy
import psycopg2

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    prevent_initial_callbacks=True,
)
app.config.suppress_callback_exceptions = True

server = app.server
server.secret_key = "my secret key"
POSTGRES_USER = "postgres"
POSTGRES_PW = ""
POSTGRES_URL = "localhost"
POSTGRES_DB = "somedb"
POSTGRES_URI = (
    f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PW}@{POSTGRES_URL}/{POSTGRES_DB}"
)
server.config["SQLALCHEMY_DATABASE_URI"] = POSTGRES_URI
server.config[
    "SQLALCHEMY_TRACK_MODIFICATIONS"
] = False  # silence the deprecation warning

login_manager = LoginManager(server)
db = SQLAlchemy(server)
accessdb = psycopg2.connect(user=POSTGRES_USER, database=POSTGRES_DB)


################################################################################
### User model including access database
################################################################################
class User(UserMixin, AccessUserMixin, db.Model):
    """
    representation of a user for this example program
    """

    __tablename__ = "users"
    __access_store__ = PostgresAccessStore(accessdb)

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


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)
