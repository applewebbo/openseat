# Public Forms

A **public form** (`PublicForm`) is the container for the path someone walks
through to apply for membership — or to book an event, since booking is an
application like any other. Several forms can coexist, each with its own
sections.

![A public form's change page](../assets/screenshots/admin-publicform.png)

In **Admin → Association and applications → Public forms** every form has:

- **Title** and **introduction** — what whoever opens the link sees
- **Slug** — the final part of the public address (`/modulo/<slug>/`)
- **Open** — when off, the page still shows but no longer accepts
  applications
- **Default** — the form preselected when an editor creates a new event
  without naming one; only one form per association can hold this

Below, the **Sections** table lists this form's whole catalogue of steps, in
the order they appear: this is where fixed sections are switched on or off,
and where custom ones already added also show up. To create new ones, or to
edit their text and fields, see [Form Builder](form-builder.md).

A brand-new form automatically receives the whole catalogue of fixed
sections, already enabled and ready to use.
