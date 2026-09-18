# Restoring a backup (disaster-recovery drill)

An untested backup is a hypothesis. Run this locally every so often — **never
in production**: `dbrestore` overwrites whatever `DATABASES` points at, and
`ENVIRONMENT` defaults to `prod`.

Needs a local Postgres. The dump was taken with `pg_dump`'s custom format
(`PgDumpBinaryConnector`), so the local `pg_restore` must be at least as new as
the server that produced it.

## Step A — verify the dump file itself (no Django)

```bash
# download the latest dump (needs the BACKUP_* vars in .env)
ENVIRONMENT=dev uv run python -c "
from dbbackup.storage import get_storage
s = get_storage()
name = 'openseat-2026-09-01-000000.dump'  # pick the newest from listbackups
open(name, 'wb').write(s.read_file(name).read())
"

pg_restore -l openseat-2026-09-01-000000.dump | grep -i "database version"

# restore into a throwaway database, never the real openseat one
createdb openseat_restore_test
pg_restore --no-owner --no-privileges -d openseat_restore_test openseat-2026-09-01-000000.dump

psql -d openseat_restore_test -c "select count(*) from members_member;
select count(*) from events_booking;
select count(*) from intake_submission;"

dropdb openseat_restore_test
```

The downloaded dump contains personal data — delete it afterwards. Backup
files are git-ignored by their `openseat-*.dump` / `openseat-*.tar` pattern.

## Step B — exercise `dbrestore` itself

Step A validates the file, not dbbackup's storage-download + Postgres-connector
chain. Testing that needs a Postgres config, and loading prod env vars to get
one is exactly the mistake that overwrites production. Use the dedicated
`ENVIRONMENT=restore` block in `core/settings.py` instead: it hard-codes the
database to a local `openseat_restore_test` and never reads `DATABASE_URL`, so
the restore cannot be aimed anywhere else.

```bash
createdb openseat_restore_test
ENVIRONMENT=restore uv run python manage.py dbrestore --noinput
ENVIRONMENT=restore uv run python manage.py dbshell -- -c "select count(*) from members_member;"
dropdb openseat_restore_test
```

Set `RESTORE_DB_USER` / `RESTORE_DB_PASSWORD` in `.env` only if your local
Postgres needs credentials (they default to `$USER` and empty).

The `restore` block sets `DBBACKUP_CONNECTORS["default"]["RESTORE_SUFFIX"]` to
`--no-owner --no-privileges`, so `pg_restore` skips the `OWNER TO` / `GRANT`
lines the prod dump carries for the prod database role. Without it, a local
cluster lacking that role would abort the whole restore, since dbbackup runs
`pg_restore --single-transaction`.

## Step C — write down the outcome

Record here what was restored, when, from which dump, and the row counts
observed, so the next drill has a baseline to compare against.

| Date | Dump | members | bookings | submissions | Notes |
| ---- | ---- | ------- | -------- | ----------- | ----- |
