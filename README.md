# OpenSeat

Django 6.1 application, server-driven (htmx + Alpine + Tailwind/daisyUI), deployed
to Coolify.

## Requirements

- Python 3.14
- [uv](https://docs.astral.sh/uv/)
- [just](https://github.com/casey/just)

No Node.js: Tailwind and daisyUI come from the standalone `tailwindcss-extra`
binary, Alpine is vendored into `static/js/`.

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
just serve      # web + background worker together
```

See [CLAUDE.md](CLAUDE.md) for the full stack and the project conventions.

## Deployment

Coolify builds the `Dockerfile` on push to `main`. `entrypoint.sh` migrates,
compiles translations, builds the CSS, collects static files, then starts
`web` + `worker` via hivemind.
