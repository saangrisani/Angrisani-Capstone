#!/usr/bin/env bash
set -euo pipefail

# Optional sanity checks
: "${DJANGO_SETTINGS_MODULE:=Vet_Mh.settings}"
: "${DJANGO_SECRET_KEY:?Missing DJANGO_SECRET_KEY}"
export DJANGO_SETTINGS_MODULE

# Collect static (WhiteNoise will serve them)
python manage.py collectstatic --noinput || true
# (Optional) SQLite migrations for demo
python manage.py migrate || true

# Start Gunicorn
exec gunicorn Vet_Mh.wsgi:application \
  --bind 0.0.0.0:${PORT:-8080} \
  --workers 2 \
  --timeout 120
