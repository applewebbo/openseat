# OpenSeat

Free and open source, self-hosted booking manager for non-profit associations.
OpenSeat handles event reservations, keeps the membership roster with CSV export,
and mails the attendance report automatically once an event is over.

Built to be run by the association itself: one container, one database, no SaaS
subscription and no data leaving the organisation.

## Features

- **Event bookings** — members reserve a seat, the organiser sees the list fill up.
- **Membership roster** — the members an association has to keep track of anyway,
  exportable to CSV for the accountant or the annual filing.
- **Automatic reports** — when an event closes, the summary goes out by email
  without anyone remembering to send it.

> **Status:** the project scaffold is in place (auth, background tasks, deployment).
> The features above are the goal, not yet the implementation.

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
