import dash_html_components as html
from flask_login import current_user

# internal
from dash_access.access.data import data_access
from dash_access.access import user


def Controlled(name: str = None, alt: str = None, component=""):
    """
    access-control for an arbitrary Dash component

    arguments
        component: 
            - object subclassing dash.development.base_component.Component or a JSON-serializable type
            - the component to return if the user has access to it
        name: str
            - the permission's unique name
            - if empty, the permission has no access control and is shown to all users
    """
    ret = html.Div()
    if not alt in [None, "div", "bad"]:
        pass

    elif not hasattr(current_user, "is_authenticated"):
        pass

    elif current_user.is_authenticated:
        permission_access = current_user.has_access(name)

        if permission_access:
            ret = component

        else:
            # RETURN A BLANK DIV, SHOWING NOTHING ON SCREEN
            if alt is None:
                pass

            # RETURN A DIV SHOWING ACCESS DENIED
            elif alt == "div":
                ret = html.Div("Access Denied")

            # REDIRECT THE USER TO THE BAD PAGE
            elif alt == "bad":
                ret = html.Div(
                    dcc.Location(id="bad-url-redirect", pathname="/bad", refresh=True)
                )

    return ret
