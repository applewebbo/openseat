# Design

Recorded from the built public form, not from intention. Scope: the `intake`
surfaces (`templates/intake/`). The rest of the project has no committed visual
system yet.

## Ground rules

- **daisyUI semantic tokens only.** No raw palette utilities for surfaces, text or
  accents; the theme is swapped per association, so a hard-coded colour breaks the
  next installation.
- **Light ground, always.** Chosen from the use scene, not the category: a parent
  on a phone, in daylight, filling a form they were sent by message.
- **The form owns its rendering.** Layout and daisyUI classes live in the Django
  form (`template_name`, `style_widgets`, `ROWS`), never re-written per view
  template. Three form templates exist: `section-form`, `person-form`,
  `statute-form`.

## Per-association theme

The association supplies three base colours; nothing else of its identity is
borrowed. They are written as custom properties in the shell and mapped onto
daisyUI tokens:

| Token | Source | Note |
|---|---|---|
| `--assoc-bright` | `colour_primary` as given | Progress line and bullets only — never carries text |
| `--color-primary` | `colour_primary` mixed 78% with `#1a1103` | The raw orange is 3.4:1 on white; the mix clears 4.5:1 |
| `--color-accent` | `colour_accent` mixed 88% with `#05100a` | Success and "sent" states |
| `--color-base-content` | `colour_neutral` | Body text |

L'Ontano's values: `#ED5C08`, `#528116`, `#4C5057`.

Page ground is `#f6f4f1` (warm paper grey); sheets are white. The contrast between
the two is what makes a sheet read as a sheet.

## Composition

One section per step, each a white sheet on the paper ground, under a sticky
header carrying the association mark and name. Maximum width `max-w-2xl`; the
header, the sheet, and the footer share it, so the page has one measure.

- **Progress**: a 1px rule under the header, filled in `--assoc-bright`, plus a
  "Passo n di m" line. Both are suppressed on the opening step, where the path
  length is genuinely unknown.
- **Sheet**: `rounded-2xl`, `border-black/5`, and a two-layer shadow
  (`0 1px 2px` contact + `0 8px 24px -12px` ambient). No hard offset shadows.
- **Actions**: back on the left as a quiet text link, primary on the right, both
  above a `border-black/5` rule. The primary never moves between steps.
- **Choices**: radios and checkboxes are full-width bordered cards with
  `has-[:checked]` filling them in `primary/5`. Never a bare radio in a list.

## Type

System stack, no webfont — an Operate surface and a no-CDN project. Hierarchy is
carried by scale, not by faces: `text-3xl`/`sm:text-4xl` bold tracking-tight for
the step title, `text-base` semibold for section headings, `text-sm` for fields
and recap rows, `text-xs` for chrome. Long-form legal text is capped at
`max-w-prose` with `leading-relaxed`.

## Browser surfaces

Themed rather than left to the browser: `::selection` in the association colour,
`:focus-visible` rings in `--color-primary` with a 2px offset, scrollbar colour
on `html`, and `tabular-nums` on every tax code, date and amount.

## Consent rendering

Consents are never a single checkbox and never pre-selected. Each is a required
two-way radio (`yes_no_field`) rendered as two cards. This is a legal
requirement, not a style: silence must not be readable as agreement.

## Draft continuity

Two mechanisms, deliberately complementary, because neither covers the other's
case:

- **Session**, for "same phone, came back": the draft token is remembered per
  browser and the landing page offers it as the primary action, with starting
  fresh demoted to an outline button beside it. Devices get shared, so the
  new-application path is never hidden.
- **Emailed link**, for "other device, or cookie gone": offered explicitly from
  every step, and sent once by the hourly sweep to drafts untouched for a day.
  Once, never twice, and never after the request is sent.

An unfinished draft dies thirty days after its last change. Views answer 410 with
a page that explains rather than an error, and the purge deletes the row — the
same data minimisation the privacy notice promises.

## Motion

One authored moment: the progress fill animates its width
(`transition-[width] duration-500 ease-out`). Everything else is a 200ms colour
transition on interactive surfaces. The other-parent block uses Alpine's
`x-collapse`, guarded by `[x-cloak]` so it never flashes open before Alpine boots.

## What this system refuses

- Cream grounds and serif display, the default rendition for a warm, family,
  child-facing subject. The association's world is a marker-drawn donkey in
  saturated orange and green.
- Imitating the association's own website. The mark identifies; the layout is
  OpenSeat's.
- Cards as page structure, kickers above headings, gradient text, glass.
