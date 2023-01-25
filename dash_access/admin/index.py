import json
from typing import no_type_check
from flask import session
import dash
from dash import callback_context, no_update
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html


def id(x: str):
    return "dash-access-admin-index-" + x


hidden = dict(display="none")

admin_layout = dbc.Container(
    dbc.Row(
        dbc.Col(
            [
                dbc.Button("Refresh", id=id("refresh"), color="info", block=True),
                # SELECT GRANT(S)
                dbc.Row(
                    dbc.Col(
                        dbc.FormGroup(
                            [
                                dbc.Label("Grant", width=2),
                                dbc.Col(
                                    dcc.Dropdown(
                                        id=id("granted-type"),
                                        options=[
                                            {"label": "Group", "value": "group"},
                                            {
                                                "label": "Permission",
                                                "value": "permission",
                                            },
                                        ],
                                        value="permission",
                                    ),
                                    width=5,
                                ),
                                dbc.Col(
                                    [
                                        html.Datalist(id=id("granted-datalist")),
                                        dbc.Input(
                                            id=id("granted-input"),
                                            list=id("granted-datalist"),
                                            placeholder="Name...",
                                        ),
                                        dbc.Button(
                                            "Add to Transaction",
                                            id=id("granted-add-button"),
                                            color="secondary",
                                            block=True,
                                        ),
                                    ],
                                    width=5,
                                ),
                            ],
                            row=True,
                        ),
                    ),
                    form=True,
                ),
                # SELECT PRINCIPAL(S)
                dbc.Row(
                    dbc.Col(
                        dbc.FormGroup(
                            [
                                dbc.Label("To", width=2),
                                dbc.Col(
                                    dcc.Dropdown(
                                        id=id("principal-type"),
                                        options=[
                                            {"label": "Group", "value": "group"},
                                            {"label": "User", "value": "user"},
                                        ],
                                        value="group",
                                    ),
                                    width=5,
                                ),
                                dbc.Col(
                                    [
                                        html.Datalist(id=id("principal-datalist")),
                                        dbc.Input(
                                            id=id("principal-input"),
                                            list=id("principal-datalist"),
                                            placeholder="Name...",
                                        ),
                                        dbc.Button(
                                            "Add to Transaction",
                                            id=id("principal-add-button"),
                                            color="secondary",
                                            block=True,
                                        ),
                                    ],
                                    width=5,
                                ),
                            ],
                            row=True,
                        ),
                    ),
                    form=True,
                ),
                # TRANSACTION SUBMIT
                dbc.Row(
                    [
                        # GRANTS
                        dbc.Col(
                            [
                                html.H2("Grant"),
                                dbc.ListGroup(id=id("granted-added")),
                                html.Div(id=id("granted-added-data"), style=hidden),
                            ],
                            width=4,
                        ),
                        # PRINCIPALS
                        dbc.Col(
                            [
                                html.H2("To"),
                                dbc.ListGroup(id=id("principal-added")),
                                html.Div(id=id("principal-added-data"), style=hidden),
                            ],
                            width=4,
                        ),
                        # SUBMIT
                        dbc.Col(
                            [
                                dbc.Button(
                                    "Submit Transaction",
                                    id=id("submit-transaction"),
                                    color="success",
                                    block=True,
                                ),
                                html.Div(id=id("submit-transaction-alert")),
                                html.Div(id=id("clear-added"), style=hidden),
                            ],
                            width=4,
                        ),
                    ]
                ),
            ]
        )
    )
)


def register_admin_callbacks(app: dash.Dash):
    @app.callback(
        Output(id("principal-datalist"), "children"),
        [Input(id("refresh"), "n_clicks")],
        [State(id("principal-type"), "value")],
    )
    def POPULATE_PRINCIPAL_DATALIST(n, principal_type):
        return [
            html.Option(value=x)
            for x in (
                set(
                    [
                        row["principal"]
                        for row in session["dash-access-admin-values"]
                        if row["principal_type"] == principal_type
                    ]
                )
                if "dash-access-admin-values" in session
                else ["test"]
            )
        ]

    @app.callback(
        Output(id("granted-datalist"), "children"),
        [Input(id("refresh"), "n_clicks")],
        [State(id("granted-type"), "value")],
    )
    def POPULATE_GRANT_DATALIST(n, granted_type):
        return [
            html.Option(value=x)
            for x in (
                set(
                    [
                        row["granted"]
                        for row in session["dash-access-admin-values"]
                        if row["granted_type"] == granted_type
                    ]
                )
                if "dash-access-admin-values" in session
                else ["test"]
            )
        ]

    @app.callback(
        [
            Output(id("granted-added"), "children"),
            Output(id("granted-added-data"), "children"),
            Output(id("granted-input"), "value"),
        ],
        [
            Input(id("granted-add-button"), "n_clicks"),
            Input(id("clear-added"), "children"),
        ],
        [
            State(id("granted-input"), "value"),
            State(id("granted-type"), "value"),
            State(id("granted-added-data"), "children"),
        ],
        prevent_initall_call=True,
    )
    def ADD_GRANTS(n_clicks, clear, input, type, added_data):
        trigger = callback_context.triggered[0]["prop_id"].split(".")[0]
        if trigger == id("clear-added"):
            if clear:
                return "", "", ""
            else:
                return no_update, no_update, no_update
        if not type or not input:
            return no_update, no_update, no_update

        if not added_data or added_data == "null":
            added_data = "[]"
        added_data = json.loads(added_data)
        added_data.append({"granted": input, "granted_type": type})

        print(added_data)
        unique_added = [json.loads(x) for x in set([json.dumps(x) for x in added_data])]
        list_data = sorted(
            unique_added, key=lambda x: (x["granted_type"], x["granted"])
        )
        list_view = [
            dbc.ListGroupItem(f"{x['granted_type']}: {x['granted']}")
            for x in added_data
        ]
        return list_view, json.dumps(list_data), None

    @app.callback(
        [
            Output(id("principal-added"), "children"),
            Output(id("principal-added-data"), "children"),
            Output(id("principal-input"), "value"),
        ],
        [
            Input(id("principal-add-button"), "n_clicks"),
            Input(id("clear-added"), "children"),
        ],
        [
            State(id("principal-input"), "value"),
            State(id("principal-type"), "value"),
            State(id("principal-added-data"), "children"),
        ],
        prevent_initall_call=True,
    )
    def ADD_PRINCIPALS(n_clicks, clear, input, type, added_data):
        trigger = callback_context.triggered[0]["prop_id"].split(".")[0]
        if trigger == id("clear-added"):
            if clear:
                return "", "", ""
            else:
                return no_update, no_update, no_update
        if not type or not input:
            return no_update, no_update, no_update

        if not added_data or added_data == "null":
            added_data = "[]"
        added_data = json.loads(added_data)
        added_data.append({"principal": input, "principal_type": type})
        unique_added = [json.loads(x) for x in set([json.dumps(x) for x in added_data])]
        list_data = sorted(
            unique_added, key=lambda x: (x["principal_type"], x["principal"])
        )
        list_view = [
            dbc.ListGroupItem(f"{x['principal_type']}: {x['principal']}")
            for x in added_data
        ]
        return list_view, json.dumps(list_data), None

    @app.callback(
        [
            Output(id("clear-added"), "children"),
            Output(id("submit-transaction-alert"), "children"),
        ],
        [Input(id("submit-transaction"), "n_clicks")],
        [
            State(id("principal-added-data"), "children"),
            State(id("granted-added-data"), "children"),
        ],
        prevent_initall_call=True,
    )
    def SUBMIT_TRANSACTION(n_clicks, principal, granted):
        if not n_clicks:
            return no_update, no_update
        principal = json.loads(principal) if principal is not None else []
        granted = json.loads(granted) if granted is not None else []

        print("submitting transaction")
        print(principal, granted)

        # return 1, dbc.Alert("Successfully submitted transaction", color='success',dismissable=True)
        return no_update, dbc.Alert(
            "Something went wrong, try again?", color="danger", dismissable=True
        )
