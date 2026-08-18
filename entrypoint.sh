#!/bin/sh
set -eu

echo "Migrating database..."
python manage.py migrate

# Recurring jobs are registered here, not in a data migration: the suite
# builds its schema with --nomigrations, so a migration would go untested.
python manage.py intake_schedule
python manage.py ops_schedule
python manage.py events_schedule

# Same reason: the role groups are a definition applied at every boot, so a
# permission granted by hand in the admin does not survive a deploy unnoticed.
python manage.py accounts_groups

echo "Compiling translations..."
python manage.py compilemessages -l it -l en --ignore=.venv

echo "Building production CSS..."
python manage.py tailwind build

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Starting hivemind..."
exec hivemind /app/Procfile
