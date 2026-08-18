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
- **Treasurer / external adviser** — receives the CSV register export for
  bookkeeping and statutory filings. Consumes output rather than using the
  interface.

## Product Purpose

OpenSeat lets a non-profit association run its own event bookings and membership
roster without a SaaS subscription and without member data leaving the
organisation. Success is an organiser who opens an event, shares one link, and
never has to chase a list: the bookings arrive on their own, and the list of who
is coming is in somebody's hands before the doors open.

## Positioning

Self-hosted and AGPL-licensed: one container, one database, run by the association
itself. Booking platforms in this space are hosted services that hold the member
register on someone else's infrastructure; OpenSeat keeps the roster — the record
an ETS/APS has to keep anyway — inside the organisation, and treats the paperwork
an APS owes anyway, the register and the door list, as built in rather than as
add-ons.

## Operating Context

- The organiser creates an event, then shares a **public per-event link**. Booking
  happens on that public page (`@login_not_required` — `LoginRequiredMiddleware` is
  global), without the member holding an account; login exists for organisers.
- **By the current statute, attending requires being a member**, so booking an
  event is applying to join. A known member is recognised by email plus tax code
  and books in two taps; anyone else walks the application and comes out with both.
  The association hopes the statute will change; the rule lives in one place.
- The register is maintained alongside events and exported to CSV over a date
  range, after the paper applications collected on the day are entered by hand.
- At **midnight on the day of an event** a background job (django-q2) mails the
  booking list to the association. It is a door checklist, not a post-event
  report: it has to arrive before, or it is useless.
- Deployment is a single Coolify-built container; the association or a friendly
  volunteer administrator installs and upgrades it.

## Capabilities and Constraints

- Confirmed scope: public membership applications, the register with CSV export,
  event bookings, and the booking list mailed before each event.
- Authentication is email-only (allauth, `accounts.CustomUser` without username).
- `LoginRequiredMiddleware` is global: every public surface must opt out explicitly.
- No CDN and no external runtime resource of any kind; assets are vendored.
- Django 6.1, server-driven, htmx + Alpine for interactivity; SQLite in dev,
  PostgreSQL in production.
- **Status:** applications, the register and event bookings are implemented.
- A member is created when the application is submitted, not when the board
  approves: gating on a meeting would stop anyone joining the evening before an
  event. `ratified_on` records the minute when it comes.
- One contact address can belong to several members — siblings enrolled by the
  same parent — so every lookup returns a list, never a single match.
- Undecided: paying the membership fee online (expected), and bulk import of the
  paper applications collected on the day of an event.

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
4. **Obligations happen by themselves.** The booking list arrives before it is
   needed and exports are one click; forgetting them must not be possible.
5. **Say only what is true.** No invented proof, no customers, no numbers — the
   project is early and states its status plainly.

## Accessibility & Inclusion

Non-technical volunteers across a wide age range, on their own devices. No formal
standard has been set; sensible defaults apply — real form labels, touch targets that
work on a phone, and legible type at default browser sizes.
