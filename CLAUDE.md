# OpenSeat

Self-hosted, open source booking manager for non-profit associations: public
membership applications, the register with CSV export, event bookings, and the
booking list mailed to the association at midnight before each event.

Django 6.1, server-driven, deployed to Coolify from `main`.

## Stack

| Layer      | Choice                                                              |
| ---------- | ------------------------------------------------------------------- |
| Runtime    | Python 3.14, Django 6.1, granian + uvloop (WSGI), hivemind           |
| Database   | SQLite in dev, PostgreSQL (`psycopg`) in prod via `DATABASE_URL`     |
| Static     | WhiteNoise (prod only) — no nginx                                    |
| Media      | volume at `MEDIA_ROOT`, served by WhiteNoise in prod                 |
| Styling    | Tailwind 4 + daisyUI through `django-tailwind-cli` — **no npm**      |
| Frontend   | htmx (vendored by `django-htmx`), Alpine (vendored), django-cotton   |
| Icons      | Phosphor, a handful of SVGs vendored into `static/img/icons/`        |
| Admin      | Django's own, themed from the association row — no third-party theme |
| Forms      | crispy-forms + crispy-tailwind, `TemplatesSetting` renderer          |
| Rich text  | django-ckeditor-5, assets shipped with the package — no CDN          |
| Auth       | allauth, email-only login, `accounts.CustomUser` without username    |
| Tasks      | django-q2 — ORM broker in dev, Redis in prod, `sync` in tests        |
| Backups    | django-dbbackup → `STORAGES["dbbackup"]`, S3-compatible or local disk |
| PWA        | django-pwa                                                           |
| Tooling    | uv, just, prek/pre-commit, ruff, djlint, djade, pytest               |

## Commands

Everything goes through `just`; every Python call goes through `uv`. **Never `pip`.**

```
just install          # uv sync
just local            # tailwind runserver
just serve            # web + qcluster + mailpit together (mprocs)
just migrate          # apply migrations
just makemigrations   # create them
just ftest            # fast parallel suite  ← the one to use
just cov              # suite + coverage, fails under 100%
just lint             # full pre-commit suite — ALWAYS before `git add`
just check            # manage.py check --deploy against prod settings — needs a
                      # .env in step with .env.example: the prod branch reads
                      # SITE_BASE_URL and DATABASE_URL, and crashes without them
just crawl            # in-process site crawl, catches dead links and assets
just messages         # makemessages + compilemessages (it, en)
just update_alpine    # re-vendor Alpine from the npm registry
just update_icons     # re-vendor the Phosphor icons
just update_all       # lock + Alpine + icons + hooks
```

## Rules specific to this project

- **No CDN, ever.** htmx comes from `{% htmx_script %}`, Tailwind/daisyUI from the
  `tailwindcss-extra` binary, Alpine from `just update_alpine` into `static/js/`,
  Phosphor icons from `just update_icons` into `static/img/icons/`.
- **The admin is themed, not replaced.** `core.admin.OpenSeatAdminSite` puts the
  association into `each_context`, so name and logo reach every page including the
  login, and `static/css/admin.css` maps Django's own CSS variables onto the
  palette `theme_css` serves from the database. Every `ModelAdmin` stays a plain
  `admin.ModelAdmin`. Django writes its dark palette as `html[data-theme="dark"]`,
  so overrides need `:root[data-theme="dark"]` to outrank it. The header's user
  tools are re-rendered in `templates/admin/base_site.html` as an account menu —
  a `details`, closed from `static/js/admin.js` — so no address is on the page and
  a phone gets logo, menu and theme toggle on one row.
- **`src/source.css` needs `@plugin "daisyui";`** — the `TAILWIND_CLI_USE_DAISY_UI`
  setting only picks the binary, it does not enable the plugin. Every directory
  holding classes needs its own `@source` line; never point one inside `.venv/`.
- After adding utility classes run `manage.py tailwind build --force` — a plain
  build reports "up to date" and skips the rebuild.
- **`just crawl` is a release gate, not a test.** It is run by hand before a release,
  with the CSS already built, and is deliberately absent from the suite and from CI.
  It walks the real site in-process and reports dead links and missing assets.
- **Media is not static.** Uploads live on a volume at `MEDIA_ROOT`;
  `core.middleware.MediaWhiteNoiseMiddleware` serves them in prod, ahead of
  `LoginRequiredMiddleware`, with `WHITENOISE_AUTOREFRESH` so a file added after
  boot is found. `check --deploy` errors when the volume is absent.
- **Backups go to `STORAGES["dbbackup"]`**, never to `DBBACKUP_STORAGE`, which
  django-dbbackup stopped reading in 4.2. `ops.maintenance` runs the daily dump
  of db and media, purges backups past `BACKUP_RETENTION_DAYS`, and deletes media
  nothing references. `manage.py ops_maintenance --dry-run` shows what it would do.
- **`DEBUG` fails closed**: strict parse, defaults to `False`. So does `ENVIRONMENT`
  (defaults to `prod`). `SECRET_KEY` has no default and crashes at startup if unset.
- **`LoginRequiredMiddleware` is on**: every public view needs `@login_not_required`.
- **Apps by concern**: `intake` is the public form engine, `members` the register,
  `events` bookings and the pre-event checklist, `ops` the scheduled housekeeping.
  Each app registers its own django-q schedule through a `*_schedule` command run
  from `entrypoint.sh`, never from a data migration: the suite runs
  `--nomigrations`, so a migration would go untested.
- **Booking an event is applying to join**, because the statute says attending
  requires membership. That rule lives in `events.views.join` and
  `Submission.event`; a statute that drops it is a small change, by design.
- **Function-based views**, one concern each.
- **Tests live in `tests/`**, never inside the apps. Factories in `tests/factories.py`,
  registered as fixtures in `conftest.py`. Mock only as a last resort.
- Templates are kebab-case; partials keep the `-partial.html` suffix. Components go
  in `templates/cotton/`.
- Freeze time with `time-machine`, never freezegun.
- **`.env` is never read or committed.** New variables go to `.env.example` and the
  user adds them to `.env` themselves.
- Settings are a single `core/settings.py` with `dev` / `test` / `prod` branches at
  the bottom — not a settings package.

## Deploy

The `deploy` job in `.github/workflows/ci.yml` runs only after `quality` passes on
`main` and calls Coolify's deploy API webhook, reading `COOLIFY_WEBHOOK_URL` and
`COOLIFY_TOKEN` from the repository secrets. Automatic Deployment stays **off** in
the Coolify application, otherwise a push deploys twice and skips the suite.

Coolify then builds the `Dockerfile` and gates on its own health check.
`entrypoint.sh` runs migrate → compilemessages → tailwind build → collectstatic, then
hands over to hivemind with the `Procfile` (`web` + `worker`). `set -eu` means a
failing step aborts the boot, so a broken migration never becomes healthy.

Keep `ARG TAILWIND_VERSION` in the Dockerfile aligned with what `django-tailwind-cli`
expects, or the first boot downloads ~120 MB and the health check times out.

Keep `ARG POSTGRES_VERSION` aligned with the major version of the database the
deploy points at. `dbbackup` shells out to `pg_dump`, which refuses a server newer
than itself, and the media backup keeps succeeding — so the failure is a silent
one until someone needs the dump.
