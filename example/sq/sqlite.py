import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from flask_login import current_user, logout_user, login_user

from dash_access import Controlled

from sqlite_setup import app, User


def login():
    return [
        dbc.Input(id="email", placeholder="username"),
        dbc.Input(id="password", placeholder="password"),
        dbc.Button("login", id="login"),
    ]


def home():
    return [
        Controlled(
            name="open",
            alt="div",
            component=dbc.Card(
                "everyone can see this", body=True, color="primary", inverse=True
            ),
        ),
        html.Br(),
        Controlled(
            name="sensitive",
            alt="div",
            component=dbc.Card(
                "sensitive information", body=True, color="info", inverse=True
            ),
        ),
        html.Br(),
        Controlled(
            name="classified",
            alt="div",
            component=dbc.Card(
                "classified information", body=True, color="danger", inverse=True
            ),
        ),
        html.Br(),
    ]


app.layout = html.Div(
    [
        html.Div("user: ", id="username"),
        dcc.Location(id="url", refresh=False),
        dcc.Link("home", href="/home"),
        html.Br(),
        dcc.Link("logout", href="/logout", id="logouts"),
        html.Br(),
        html.Div(id="content"),
    ]
)


@app.callback(
    Output("url", "pathname"),
    [Input("login", "n_clicks")],
    [State("email", "value"), State("password", "value")],
)
def login_(n_clicks, email, pw):
    existing_user = User.get(email)
    if existing_user:
        if existing_user.check_password(pw):
            login_user(existing_user)
        return "/home"
    return dash.no_update


def user_name():
    return "user: " + (current_user.name if current_user.is_authenticated else "")


@app.callback(
    [
        Output("content", "children"),
        Output("logouts", "style"),
        Output("username", "children"),
    ],
    [Input("url", "pathname")],
)
def router(url):
    if url == "/home" or url == "/":
        if current_user.is_authenticated:
            return home(), {}, user_name()
    if url == "/login":
        if current_user.is_authenticated:
            return home(), {}, user_name()
    if url == "/logout":
        if current_user.is_authenticated:
            logout_user()
        return (
            dcc.Location(id="temp-logout-url", pathname="/login"),
            dict(display="none"),
            user_name(),
        )

    return login(), dict(display="none"), user_name()


if __name__ == "__main__":
    app.run_server(debug=True)
