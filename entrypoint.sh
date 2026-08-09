#!/bin/sh
set -eu

echo "Migrating database..."
python manage.py migrate

echo "Compiling translations..."
python manage.py compilemessages -l it -l en --ignore=.venv

echo "Building production CSS..."
python manage.py tailwind build

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Starting hivemind..."
exec hivemind /app/Procfile
