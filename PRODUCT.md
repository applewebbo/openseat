# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Three audiences, in descending order of time spent in the product:

- **Organiser** (primary) — the volunteer or secretary of a non-profit association
  who creates events, keeps the membership roster up to date and exports it. Works
  mostly from a desktop, often in the evening, a few times a month. Not technical,
  never trained on the tool.
- **Member booking a seat** — an association member who reserves a place at an
  event, typically on a phone, in seconds, arriving from a link shared by the
  organiser (email, WhatsApp, social). Does not necessarily have an account.
- **Treasurer / external adviser** — receives the CSV roster export and the
  attendance reports for bookkeeping and statutory filings. Consumes output rather
  than using the interface.

## Product Purpose

OpenSeat lets a non-profit association run its own event bookings and membership
roster without a SaaS subscription and without member data leaving the
organisation. Success is an organiser who opens an event, shares one link, and
never has to chase a list or remember to send the attendance report: the reservation
list fills itself and the report is mailed automatically when the event closes.

## Positioning

Self-hosted and AGPL-licensed: one container, one database, run by the association
itself. Booking platforms in this space are hosted services that hold the member
register on someone else's infrastructure; OpenSeat keeps the roster — the record
an ETS/APS has to keep anyway — inside the organisation, and treats the automatic
attendance report as a built-in obligation rather than an add-on.

## Operating Context

- The organiser creates an event, then shares a **public per-event link**. Booking
  happens on that public page (`@login_not_required` — `LoginRequiredMiddleware` is
  global), without the member holding an account; login exists for organisers.
- The roster is maintained alongside events and exported to CSV for the treasurer
  or the annual filing.
- When an event closes, a background job (django-q2) mails the attendance summary
  automatically — no one has to remember it.
- Deployment is a single Coolify-built container; the association or a friendly
  volunteer administrator installs and upgrades it.

## Capabilities and Constraints

- Confirmed scope: event bookings, membership roster with CSV export, automatic
  attendance report by email.
- Authentication is email-only (allauth, `accounts.CustomUser` without username).
- `LoginRequiredMiddleware` is global: every public surface must opt out explicitly.
- No CDN and no external runtime resource of any kind; assets are vendored.
- Django 6.1, server-driven, htmx + Alpine for interactivity; SQLite in dev,
  PostgreSQL in production.
- **Status:** the scaffold is in place (auth, background tasks, deployment). Events,
  bookings, roster and reports are the goal, not yet implemented.
- Undecided: how a member identifies themselves on the public booking page (name and
  email versus a link to an existing roster entry), and how a booking is cancelled or
  changed after the fact.

## Brand Commitments

- Name: **OpenSeat**. Free and open source, AGPL-3.0-or-later — the licence is part
  of the pitch, not a footnote.
- Interface language is **Italian** (`lang="it"`), with English as the second locale;
  every string ships through i18n. Terminology in Italian: *soci*, *eventi*,
  *prenotazioni*, *presenze*.
- Tone: plain and unceremonious. Users are volunteers, not customers.

## Evidence on Hand

- README.md and CLAUDE.md describe the product and the stack.
- No logo, no photography, no customer names, no testimonials, no benchmarks, no
  pricing, no deployment references exist. Future work must not fabricate any of
  them.

## Product Principles

1. **The roster never leaves the association.** Self-hosted, no SaaS, no CDN, no
   third-party runtime call — this is the reason the product exists.
2. **Built for volunteers who use it rarely.** Every screen must be usable without
   training and without memory of the last visit, months earlier.
3. **The public booking path is the product's front door.** It is reached on a phone,
   from a shared link, by someone with no account and no patience.
4. **Obligations happen by themselves.** Attendance reports and exports are automatic
   or one click; forgetting them must not be possible.
5. **Say only what is true.** No invented proof, no customers, no numbers — the
   project is early and states its status plainly.

## Accessibility & Inclusion

Non-technical volunteers across a wide age range, on their own devices. No formal
standard has been set; sensible defaults apply — real form labels, touch targets that
work on a phone, and legible type at default browser sizes.
