import dash_html_components as html
from flask_login import current_user

# internal
from dash_access.access.data import data_access
from dash_access.access import user


def Controlled(name: str = None, alt: str = None, component="", custom_value="", func=None):
    """
    access-control for an arbitrary Dash component

    arguments
        component: 
            - object subclassing dash.development.base_component.Component or a JSON-serializable type
            - the component to return if the user has access to it
        name: str
            - the permission's unique name
            - if empty, the permission has no access control and is shown to all users
        alt: str
            - blank | "div" | "bad" | "custom"
            - how to handle user lacking access
            - values
                blank: return `""` (most common)
                `"div"`: return an `html.Div` that says `"Access Denied"`
                `"bad"`: return a link that sends the user to your /bad URL (customizable - useful for full-page control)
                `"custom"`: return a custom value defined in the `custom_value` parameter
        custom_value: 
            - object subclassing dash.development.base_component.Component or a JSON-serializable type
            - something custom to return if the user doesn't have access
            - only used if alt="custom"
        func: 
            - a function used to check if the user has access
            - use if you don't want to use the current_user system
    """
    ret = html.Div()
    if not alt in [None, "div", "bad", "custom"]:
        pass

    elif not hasattr(current_user, "is_authenticated"):
        pass

    elif current_user.is_authenticated:
        if func is None:
            permission_access = current_user.has_access(name)
        else:
            permission_access = func(name)

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

            elif alt == "custom":
                return custom_value

    return ret
