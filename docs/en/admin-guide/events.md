# Events

Every initiative the association runs — a trip, an open day, a workshop —
is an **event** (`Admin → Events and bookings → Events`), with its own
public page and its own application form.

![An event's create/edit form](../assets/screenshots/admin-event-form.png)

## Main Fields

- **Title** and **description** (with a rich-text editor) — also generates
  the public page's slug automatically
- **Location**, **start date and time**, estimated **duration** in hours
- **Image** — a wide picture, at least 1200 px; the square version used in
  previews is cropped from it automatically
- **Application form** — which form whoever books fills in; left empty, the
  association's default form is used
- **Published** — when off, the event does not show on the home page and
  cannot be reached from its direct link
- **Suggested cost** — not shown to the public yet, just an internal
  reminder

## Requires Membership

This switch decides whether completing a booking creates or updates a
member register entry, once check-in confirms it:

- **On** (default) — by statute, attending is the same as joining: once
  check-in confirms it, the person enters or stays on the member register
- **Off** — the event becomes a plain booking: the form to fill in stays
  the same, but no member is ever created or updated

Useful for events open to non-members too, where asking for the full
membership application would not make sense. Covered in more depth in
[Form Builder](form-builder.md#booking-without-joining).

## Check-in and Checklist Sent

Two read-only fields track what happened on the day of the event: when the
booking list was sent (automatically, at midnight before the event), and
when an editor opened check-in at the door. They cannot be edited from here
— they are shown, but managed from the event's own page, described in
[Check-in on the Day of the Event](checkin.md).
