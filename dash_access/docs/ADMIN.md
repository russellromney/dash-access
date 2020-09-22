# Administration with Dash Access

The admin dashboard allows the administrator to control users' access to permissions. You can create and edit users and groups and view/delete/approve signups from the dashboard.

If you're logged in as the admin, you'll see two different things: there is a "refresh" button in the navbar and you'll see an "admin" link in the navbar user dropdown. Those are controlled by the `navBar()` callback in `application.py` which checks the current user; if their `id` is `admin`, they get those goodies.

The dashboard is an permission itself; the admin is the only one granted access to it (though others can also be granted access; you'd need to change the `navBar()` callback slightly).

# User flow

What does a non-admin user see?

**Login**

The user can enter their email/password, click "Sign Up", or click "Forgot Password". The navbar shows links to the login and signup pages. If the login works, they get sent to `/home` via the `router()` function in `application.py`.

**Forgot Password**

The user can click a button to reset their password after entering their email. If the email doesn't exist, they'll see a "something went wrong, check that email" failure message. If it works, it will send them an email with a randomly generated password - using the standard `uuid.uuid1().hex` hash hexdigest.

**Signup**

The user sees all the fields. All required fields contain an asterisk. If any of these are missing, they get a warning upon clicking submit. Certain values are validated: phone and mobile are checked for local standard based on their country, using the excellent `phonenumbers` package. Their email is validated for format with the excellent `validate_email` package. Required values cannot be blank or None.

They can click the button to verify their email with a code anytime after putting their email in. I elected to do this rather than a separate verify page, as the verify code is just a deterministic hash of their email - it will be fine to sign up again later.They must agree to terms and conditions which pop up in a `dbc.Modal` component. 

If they click the submit button before all of these are done, they'll get a warning telling them what's wrong in approximate order of importance.

If their signup is successful, the inputs and submit button are hidden and a table of their details shows up along with another link to open the terms and conditions. The administrator is emailed a notification that the user at that email has signed up.

**Profile**

The user can view and change all their info, except for  their email. Emails cannot be changed.

Changing their password requires them to input their old password correctly, enter a new password, and confirm their new password. New passwords must be > 7 characters.


# Administrative Flows

Now that we know what the user sees we can move on to admin tasks. After any change, click the "refresh" button to load the change into the admin session. Then click the tab's load button again to reload with the updated values. The tabs maintain state if you navigate away from one to another tab, but not if you change pages.

## Add User

The default tab in the dashboard is Add User. It's the same flow as the signup. The same required fields and value validation apply to values here. Perhaps a "required value override" checkbox would be helpful to reduce the monotony/beauracracy here. Various warnings are issued to guide your input. If successful, the user is created. Click one of the "refresh" buttons to reload the users and groups, including the new user. Click the "clear inputs" button to clear all the input fields.

> NOTE: You can add a user with the same email as a pending signup; however, a user cannot sign up with an email if a user already exists with that email.

## Edit User

The next tab is User Info/Edit. You can make any changes you want, subject to slightly weaker validation and requiry constraints as in signup & adding a user. Each section has its own submit button so as to lower the likelihood of stupid developer errors in building the functions. Any change that doesn't succeed entirely is immediately rolled back. You can click a button to easily reset a user's password (emails to them).

In this screen you, can also grant or remove a user's groups and permissions. You can see which groups and permissions are granted directly to them as well as all that they are granted access to, including recursively through groups. 

At the end of the page is a button to delete the user if you so choose.

## Add Group

The only thing you need to add a group is a unique name. If you want to add the rest, go for it. Errors in input will trigger associated warnings.

## Edit Group

The Group Info/Edit tab is the most complex, but it's really just a superset of the User Info/Edit tab. It even shares most of its code - the only difference is that you can add users to a group in addition to other groups (called "Inherits") and permissions. You can see which permissions the selected group has access to, both directly and through group membership. You can delete the group if you need.

## Signups

The Signups tab label shows green if there are any signups, plus a counter representing the number of pending signups. The page is quite simple: you can either do nothing, delete, or approve each signup. You'll need to check the "are you sure?" box before approving or deleting a signup.

The list of signups are sorted descending by signup date (newest first) in the table below the select/approve/delete interface. The user's signup information is displayed there. 

> NOTE: The user had to verify their email in order to sign up; thus all pending users in the signups table have verified emails.

After completing an operation, click "refresh" to load the updated signup list and load the newly created user/newly delete signup into/out of memory.

