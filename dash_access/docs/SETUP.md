# Setting Up Dash Access

There are several steps to setting up development with Dash Access.

## Environment

For local developmnet, you'll need the environment variables specified in README.md in a dotenv file in the root directory of the project. I left the ones I used in the project root.

Dev is where you build local features and test out layouts, etc. Very little setup is necessary.

For dev: `env/.env-dev`

Stage is where you test the features in a prod-like setting. Test adding users, access control, visuals, etc. here. You'll need to run `aws configure` or have a default profile in `~/.aws/credentials` (on UNIX; unsure for PC) set up for the `boto3` package to work correctly. You can deploy the code in the cloud to test for cloud-specific bugs without hitting your production data at all.

For stage: `env/.env-stage`

Required environment variables are:

| Name | Details |
| --- | --- |
| APPLICATION_ENVIRONMENT | DEV, STAGE |
| USERS_TABLE | the name of the users table |
| GROUPS_TABLE | the name of the groups table |
| SIGNUPS_TABLE | the name of the signups table |
| LOGGING_TABLE_ACCESS_EVENTS | the name of the table where the access event logs are stored |
| LOGGING_TABLE_LOGIN_EVENTS | the name of the table where the login event logs are stored |
| EMAIL_API_KEY | Your developer key for transactional email |
| EMAIL_API_SECRET | Your developer secret for transactional email |
| EMAIL_APP_NAME | The application's name as shown in emails, e.g. Dash Access |
| FROM_EMAIL | The FROM email in password reset emails |
| ADMIN_NOTIFICATION_EMAIL | The email to send admin notifications to |

If you're testing things out in a Jupyter Notebook or terminal, etc., you'll need the environment variables to use any access functionality. It's easy to set up your environment with `dev_utils.setup_env('env/.env-de')` or whichever dotenv file you'd like to use. It adds the vars/vals in your dotenv to `os.environ` for global interpreter access.

> TIP: if you doing anything in interactive Python that interfaces with the access system, you'll need to setup the environment with `from utils import dev_utils` and `dev_utils.setup_env('.env')`

## Application Modes

You can run `application.py` in dev, stage, or prod mode with command line flags, like:
```
# dev
python application.py -dev

# stage
python application.py -dev

# prod
python application.py
```

This automatically sets up your environment variables using the helper function `utils.dev_utils.setup_env()`.

In production you'd just pass the `application:application` object to a WSGI server, and it skips the flags altogether.

## Database setup

You'll need to set up the database fields before you launch the app, specifically to create the admin user that has all-power access.

**Dev**

To run in dev mode, you'll need to initialize the database tables first. This creates the SQLite tables for logging (access and login events) and access (participants: users, groups, signups) with some fake data. I encourage you to change that data to your liking.

```python
# dev - creates tables and values in data/local.sqlite3
from utils import dev_env
dev_env.create()
```

**Stage**

To use the stage environment, you'll need to create stage tables in DynamoDB first. I recommend using on-demand tables as they will be cheapest for your use case and will never throttle you if there is ever a burst of activity. You can name them anything you want, but I recommend something like `stage-groups` or something easy.

| For | Key & Type | Sort Key & Type|
| --- | --- | --- |
| users | email, string | |
| groups | name, string | |
| signups | email, string | |
| access events | email, string | ts, number |
| login events | email, string | ts, number |

```python
# stage - creates values in DynamoDB
# tables need to be created first
from utils import stage_env
stage_env.create()
```

## Legal

You'll need to add your terms and conditions to `utils/legal.py` in Markdown for them to show up in the signup page (as currently designed). The terms currently show up in `pages.signup` in the `terms1` and `terms2` modals components.

## Ignoring errors

Depending on your Python IDE, you might see the following "errors" in a code checker:
- `Instance of '' has no 'Table' member`
  - where:
    -  `system/utils/stage_clients.py`
    -  `system/utils/clients.py`
  - why: 
    - `boto3` has something weird where it doesn't show the resource as having any classmethod classes until you instantiate the resource; annoying, but it works fine
- TBD