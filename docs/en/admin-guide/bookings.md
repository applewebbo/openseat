# Bookings

Every place booked for an event — through the public form or added by hand
by an editor — is a row in **Admin → Events and bookings → Bookings**,
filterable by event and searchable by name.

![The bookings list](../assets/screenshots/admin-bookings-list.png)

## Adding a Booking by Hand

When someone needs to be registered without going through the public form —
a phone call, a last-minute sign-up — a booking can also be created from
here. A **Send the confirmation mail** option (on by default) decides
whether to notify the person, useful to turn off for bookings that should
not trigger a notification.

## A Booking's State

- **Confirmed on** — filled in once check-in confirms it (see
  [Check-in on the Day of the Event](checkin.md)); until then, the booking
  is only announced, not yet attended
- **Cancelled on** — a cancelled booking is not deleted: it stays on record
  as a history of who had booked and when they withdrew

The **Application** field links a booking made through the public form to
its related application, useful for tracing back every answer given; it is
read-only because the link is created automatically on booking.
