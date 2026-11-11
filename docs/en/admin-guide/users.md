# Users and Permissions

Whoever runs the association day to day has their own account, assigned one
of two predefined roles in **Admin → Back-office users → Users**. Login is
email-only, with no username.

![The users list](../assets/screenshots/admin-users-list.png)

## The Two Roles

- **Editor** — can create and change events, add and change bookings (not
  delete them: a booking is cancelled, not deleted, so there is a trace of
  who had booked)
- **Editor+** — everything an Editor can do, plus exporting the members
  acquired at an event: a sensitive operation on personal data, not
  necessarily one to hand to every volunteer at the door

A group is assigned from the user's own page, in the permissions section.

![Assigning groups on a user](../assets/screenshots/admin-user-groups.png)

## The Superuser

A superuser (such as the first account created on install) sees and changes
everything, including the association's settings and the form
configuration: it is the role for whoever technically runs the installation,
not for day-to-day use.
