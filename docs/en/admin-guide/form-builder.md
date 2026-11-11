# Form Builder

The **public form** is the multi-step path (sections) someone walks through to
apply for membership, or to book a place at an event. Seven sections ship
ready to use; you can add more custom ones without a deploy, straight from
admin.

## The Fixed Sections

Every form starts with these seven sections, in the order they appear:

1. **Who is attending** — for themselves, or on behalf of a minor/someone else
2. **Your details** — the anagraphic details of whoever signs the application
3. **Who is attending** (member) — the minor's anagraphic details, when
   different from the signatory
4. **Statute and fee** — accepting the statute and the membership fee
5. **Privacy notice** — the GDPR notice text
6. **Image consents** — the two consents for photos/videos (website and
   WhatsApp)
7. **Review and signature** — the final signature

!!! info "The structure stays fixed"
    How these seven sections behave — who sees which, when a minor's
    application needs a second parent, the validation rules — is part of the
    code and not editable from admin. What you **can** change for each one:

    - **switch it on or off** for a given form (except the final signature,
      always present)
    - the **title** shown on that step (the *Title* field)
    - for **Statute and fee** and **Privacy notice**, the actual **text**
      shown (the *Custom text* field, with a rich-text editor) — left blank,
      it falls back to the stock copy
    - for **Image consents**, the two consent **labels** (*Image consent
      label* and *WhatsApp consent label* fields)

To edit one, go to **Admin → Association and applications → Sections**, pick
the section of the form you want, and save.

## Adding a Custom Section

When the seven fixed sections are not enough — say you want to ask which time
slot an applicant prefers — you can add your own.

1. Go to **Admin → Association and applications → Sections → Add section**
2. Choose the **form** it belongs to
3. Write a **title** (required: it also generates the section's technical
   slug — if another title would generate the same slug, a number is
   appended)
4. Set the **order** (a lower number shows first) and whether it is
   **enabled**
5. Save

![The form for adding a new section](../assets/screenshots/admin-section-add.png)

!!! warning "Mind the order relative to the review step"
    The **Review and signature** section is always the last step the form
    reaches. If your custom section's order is higher than the review
    step's, it ends up after the signature and nobody filling in the form can
    ever reach it. Check the other sections' current order in the list
    before saving.

Once saved, the page shows a **Custom fields** table — that is where you add
this section's questions.

## Adding Fields to a Custom Section

From the section's page, click **Add another Custom field** and choose:

- **Label** — the question shown to the applicant
- **Help text** — an optional line shown under the question
- **Type** — one of:
  - *Short text* — a single line of free text
  - *Long text* — multiple lines of free text
  - *Single choice* — a dropdown with the options you define
  - *Multiple choice* — the same, but several options can be picked together
  - *Checkbox* — a yes/no question
  - *Numeric value* — a number, decimals included
- **Required** — if checked, the form will not move on until it is answered
- **Order** — the order of the questions within the section

![A custom section with its fields](../assets/screenshots/admin-section-custom-fields.png)

For the **Single choice** and **Multiple choice** types you also need to
define the options: save the field, then open its own page (**Admin →
Association and applications → Custom field**, or the link from the
section's table) and add rows under **Choices**, each with its own label and
order.

![A single-choice field's options](../assets/screenshots/admin-customfield-choices.png)

Each applicant's answers stay attached to their own application and show up
alongside the rest of it in the application's admin detail page.

## Previewing a Section

Before publishing a section — fixed or custom — you can see what it will
actually look like without leaving admin. At the bottom of the change page
there is a **Preview** box, collapsed by default so it does not take up
space: click **Show the preview** to open it.

![The Statute and fee section's preview, open](../assets/screenshots/admin-section-preview.png)

It is a snapshot of what is saved, not a live preview: to see the effect of
a change to the title or the text, save the page first.

## Booking Without Joining

An event does not have to require becoming a member to attend it.

On **Admin → Events and bookings → Events**, every event has a **Requires
membership** switch:

- **On** (the default) — completing the form and checking in at the door
  creates or updates an entry in the membership register
- **Off** — the event becomes a plain booking: attendees still fill in
  whichever form the event uses, but no member is ever created or updated,
  even after check-in

Useful for events open to non-members too — an open evening, a public event —
where asking for the full membership application would not make sense.
