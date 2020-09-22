# Overview of Dash Access

What I'm calling "Dash Access" is a system that enables quickly developing Dash 
applications that allow an administrator to control access to the contents of the
pages. It does this in two ways:

1. Developer experience
2. Simple administration

The goal of the project is to get the access system out of the way of the developer
and out of the schedule of the administrator, remaining safe and reliable, and 
automating the annoying stuff like notification emails.

Read the docs like:
- OVERVIEW
- STRATEGY: how should I think about mapping access?
- ADMIN: get a sense of the system's user-facing operations
- SETUP: how do I start?
- DEVELOPMENT: how to code using the system

## Access Principles

Dash Access is built for access control first. The principles driving this control are:

1. Access must be granted directly or through group membership
2. Access is granted to permissions and data permissions
3. The system is blind to the existence of permissions and data permissions - it just checks whether the user can access them or not
4. Access is checked for permissions and data permissions every time they are displayed - permissions are never cached or held in a session variable on the client or server
5. All access activity is logged

## Development Principles

Dash Access is built for the developer. 

1. It enforces "better practices" in development, e.g. there are structures built for local development, non-prod development (stage), and final prod checking. ff
2. Minimal code over normal development.
3. Avoid access database interactions.
4. Extensible parts

## Project Structure

The system is built on Dash. The main files are:

`app.py`: create the Dash app instanace

`application.py`: initialize the app's addons (e.g. login management), create the base layout, setup local environments, and run the application in `__main__`

`requirements.txt`: Python package requirements

`env/.env`: the production environment variables (not required - the environment variables just need to exist)

`env/.dev-env`: the local development environment variables

`env/.stage-env`: the local development environment variables to test production

---


The access system is organized within the `system/` folder in functional
directories. Those files/directories are:

### `access/`

Modules for managing direct participants in the access system.

`control`: permission access control

`data`: manage data access and sourcing

`group`: manage groups

`signup`: manage self-service signups

`user`: manage users and all user actions including logging for attempts to access permissions and login


### `auth/`

Modules for managing user authentication and user session status.

`auth`: authenticate a user

`pw`: wrappers for high-strength password authentication using bcrypt (very slow, strong password protection)

`user`: the authenticated user session object

### `utils/`

Modules for developer ease and lower-level objects.

`clients`: classes for prod (DynamoDB) DB operations of access and logging; functions cannot be run locally, rather they must exist as part of the app; very fast shared connections

`dev_utils`: functions that make the system code more concise, e.g. standard DB change operations with rollbacks on errors, a system-similar alert component `toast()`, a DB operation function factory, and shortcuts for returning the local dev/stage DB to the user or the app context

`dev_clients`: classes for local (SQLite) DB operations of access and logging; only run locally, very fast for development

`stage_clients`: classes for testing prod (DynamoDB) DB operations of access and logging, with a slower connection that can be run locally and test cloud functionality

`dev_env`: tools for setting up the developer environment locally

`stage-env`: tools for setting up the stage environment locally/in the cloud

`legal`: keep legal information here, e.g. terms and conditions

`utils`: developer shortcuts

### `pages/`

The pages that make up the access and auth system; these are kept in the system folder to get out of the way of the developer's application pages.

`admin`: user, signup, and access administration

`bad`: bad page request sign

`forgot_password`: self-service password reset

`login`: login, go to signup, or manage forgotten password

`profile`: user sees and edits their personal info

`signup`: where new users sign up

### `docs/`

Documentation.



## Wishlist

Some things I have not finished that I wanted to add for usability and well-roundedness:

- ability to see all users who have access to permission X
- a chart/table showing some path of access; e.g. group N inherits group A inherits group C has access to Y
- bulk updates to groups
- bulk updates to users
- automatic permission tree
- admin can see chart of a user's logins
- admin can see chart of all logins over time
- admin can see chart of all access attempts over time
- admin can see chart of a user's access attempts over time
- admin can see chart of all access attempts over time by permission, user, and date, etc.
- session analytics - time spent, permissions looked at the most, etc.
- more than QA-like tests - need rigor