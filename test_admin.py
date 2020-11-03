import dash_bootstrap_components as dbc
import dash
from dash_access.admin.index import admin_layout, register_admin_callbacks

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
)

app.layout = admin_layout
register_admin_callbacks(app)

if __name__ == "__main__":
    app.run_server(
        debug=True,
        port=5000,
    )