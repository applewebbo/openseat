# OpenSeat

Free and open source, self-hosted booking manager for non-profit associations.
OpenSeat takes membership applications, keeps the register with CSV export, and
mails the booking list before each event.

Built to be run by the association itself: one container, one database, no SaaS
subscription and no data leaving the organisation.

## Features

- **A public home page** — the association's logo, name, title and description,
  written in the admin with a small rich-text editor, above the next date in
  full and the other open ones under it. Past dates stay listed, smaller. Empty
  sections are simply not drawn.
- **Public membership application** — one section per step, from a link anyone can
  open, with the parental-responsibility and image-consent rules an Italian APS
  actually has to follow. Drafts survive a lost connection and expire after thirty
  days.
- **Membership register** — every submitted application becomes an entry, ready
  for the board to minute, exportable to CSV over a date range for the accountant
  or the annual filing.
- **Event bookings** — a member proves who they are with their email and tax code
  and books a place for everyone in the family. Someone new joins and books in the
  same flow, because by the current statute you cannot attend without being a
  member.
- **The list, before the event** — at midnight on the day of an event the booking
  list is mailed to the association, so whoever is on the door has it in hand. It
  is a checklist, not a report: nobody has to remember to ask for it.

> **Status:** applications, the register and event bookings work end to end.
> Not built yet: paying the membership fee online, and bulk import of the paper
> applications collected on the day.

## Requirements

- Python 3.14
- [uv](https://docs.astral.sh/uv/)
- [just](https://github.com/casey/just)
- [mprocs](https://github.com/pvolok/mprocs) and
  [mailpit](https://mailpit.axllent.org/), for `just serve` — `just local` needs
  neither

No Node.js: Tailwind and daisyUI come from the standalone `tailwindcss-extra`
binary, Alpine is vendored into `static/js/`.

The app sends mail while you use it — the application receipt, the link back into
a draft, the consent request to a second parent — and in development that goes to
SMTP on port 1025. Without a catcher listening there every send fails with a
refused connection, which is why `just serve` starts one.

## Getting started

```bash
cp .env.example .env      # then fill in SECRET_KEY at least
just install
just migrate
just seed_demo            # example association, form and events — development only
just local                # http://127.0.0.1:8000
```

Generate a secret key with:

```bash
uv run python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
```

## Day-to-day

```bash
just ftest      # test suite
just cov        # coverage, fails under 100%
just lint       # pre-commit suite — run before `git add`
just crawl      # in-process crawl, finds dead links and assets
just check      # manage.py check --deploy against production settings
just serve      # web + worker + mailpit (inbox on http://localhost:8025)
```

See [CLAUDE.md](CLAUDE.md) for the full stack and the project conventions.

## Deployment

Coolify builds the `Dockerfile` on push to `main`. `entrypoint.sh` migrates,
compiles translations, builds the CSS, collects static files, then starts
`web` + `worker` via hivemind.

## License

Copyright (C) 2026 Enrico Bonardi

OpenSeat is free software: you can redistribute it and/or modify it under the terms
of the GNU Affero General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later version.
See [LICENSE](LICENSE) for the full text.

The AGPL covers network use: if you host a **modified** version of OpenSeat and let
other people use it over a network, you have to offer them its source code.
Installing and running it unmodified — the normal case for an association — carries
no such obligation beyond pointing users at this repository.
