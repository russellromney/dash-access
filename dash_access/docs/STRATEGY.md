# Strategies

Before getting into admin mechanics, some strategy. And first, some notes:
- permissions are anonymous and plain text; they *only exist in grants to users and groups, and in the `control.permission` values*
- this means the admin has to be careful about overlapping names and grants
- granting access to users is tedious, inefficient, and boring
- granting access to groups, then putting multiple users in those groups, minimizes the tedium
- group and permission names are just strings and can have spaces
- changing permission names is as easy as changing the name in control.permission and granting access; extra permissions building up in the closet is not a terrible thing if there are no permissions attached to it
- the admin has access to all permissions; look at the admin User Info/Edit tab to see all permissions

## Create "private" groups for users of one organization

Suppose that 5 companies pay for access to your software. Each company should have a single group in which all company members are a part. This keeps the groups together. The name should be clearly a company group, e.g. `"Company Something"` to be easily searchable and identifiable.

That company group should be granted the permissions that are common to the whole group.

The same idea applies for university classes, government user departments, etc. This allows you to answer questions like e.g. "who are all the users from Company A?"

## Create "common" groups by access level, granted to many private groups

Some combinations of access are going to be common accross private groups. Those access rights should be put into "common" groups that are granted to many other groups and users. This removes much of the tedium of manually going through editing access, user by user.

**Example**

Company A Group:
- users: A1, A2

Company B Group:
- users: B1, B2

Company A and Company B both pay for the same level of access. So do:

Create group:
- name: Common Access Group:
- permissions: permission1, permission2, permission3

Grants:
- Company A Group inherits Common Access Group
- Company B Group inherits Common Access Group

Now users A1, A2, B1, B2 all have access to permission1, permission2, and permission3. When a new client, Company C, signs up with the same level of access, you'll just need to create Company C Group and have it inherit Common Access Group. Easy.


## Create "limited private" groups by access level within private group; grant "common" groups to them

Within private groups, there will be shared levels of access that either a) align within the private group and/or b) align with other private group's access structures. Create "limited private" groups composed of a subset of that private group's users.

Then, grant common groups to those groups if there is alignment. Grouping within private groupsmakes it easier to reason about who gets what access from where, and why.

**Example**

Similar to the last example, Company A and Company B both pay for the same level of access. So do:

Company A Group:
- users: A1, A2

Company B Group:
- users: B1, B2

However, each company splits up their access by paying for two different levels of access. It's simpler to reason about groups that contain only users from one company, so create private groups that align with common groups, but are limited to only one company's users. Do:

Create common groups:
- name: Common Access Group Y:
- permissions: permission1, permission2

- name: Common Access Group Z:
- permissions: permission3, permission4

Create "limited private" groups:
- name: Company A Limited Y:
- users: A1

- name: Company A Limited Z:
- permissions: A2

- name: Company B Limited Y:
- users: B1

- name: Company B Limited Z:
- permissions: B2

Grants:
- Company A Limited Y inherits Common Access Group Y
- Company A Limited Z inherits Common Access Group Z
- Company B Limited Y inherits Common Access Group Y
- Company B Limited Z inherits Common Access Group Z

Now users A1 and B1 all have access to permission1 and permission2, while users A2 and B2 have access to permission3 and permission4. When a new client, Company C, signs up with the same level of access, you'll just need to create Company C Group, duplicate Company A Limited Y and Company A Limited Y, and add the correct users.

## Minimize individual grants of any kind

Granting a single user some access will be boring and tedious, I can almost guarantee it.