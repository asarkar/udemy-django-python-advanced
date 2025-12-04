#!/usr/bin/env bash
set -euo pipefail

: "${PORT:=8000}"

printf "Waiting for database...\n"
python manage.py wait_for_db --timeout 60

printf "Running migrations...\n"
python manage.py migrate --noinput

printf "Collecting static files...\n"
python manage.py collectstatic --noinput

printf "Starting Gunicorn on port ${PORT}...\n"
exec gunicorn app.wsgi:application \
    --bind 0.0.0.0:"${PORT}" \
    --workers 2 \
    --worker-class gthread \
    --threads 2 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile - \
    --capture-output \
    --log-level info
