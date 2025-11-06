# Dockerfile (cleaned & production-ready)
# Helped and cleaned up by ChatGPT (GPT-5) on 2025-11-06.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8000

WORKDIR /app

# (Optional) netcat only if you actually wait-for-db; otherwise remove this line
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Install deps first for better layer caching
COPY requirements.txt /app/
RUN python -m pip install --upgrade pip && pip install -r requirements.txt

# Copy code
COPY . /app/

# Create non-root user for security
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Basic healthcheck (Gunicorn must be up)
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
  CMD python -c "import os, sys, urllib.request; port = os.environ.get('PORT','8000'); try: with urllib.request.urlopen(f'http://127.0.0.1:{port}/', timeout=4) as r: sys.exit(0 if r.status < 500 else 1); except Exception: sys.exit(1)"

# Run migrations, collectstatic, ensure superuser (idempotent), then start Gunicorn
CMD bash -lc "\
  echo '▶ migrate' && python manage.py migrate --noinput && \
  echo '▶ collectstatic' && python manage.py collectstatic --noinput || true && \
  echo '▶ ensure superuser (if DJANGO_SUPERUSER_* set)' && \
  python manage.py shell -c \"import os; from django.contrib.auth import get_user_model; User=get_user_model(); u=os.environ.get('DJANGO_SUPERUSER_USERNAME'); e=os.environ.get('DJANGO_SUPERUSER_EMAIL'); p=os.environ.get('DJANGO_SUPERUSER_PASSWORD'); \
    print('  · skipping (env vars missing)') if not (u and e and p) else ( \
      print('  · exists:', u) if User.objects.filter(username=u).exists() else (User.objects.create_superuser(u,e,p), print('  · created:', u)) )\" && \
  echo '▶ gunicorn' && \
  exec gunicorn Vet_Mh.wsgi:application --bind 0.0.0.0:${PORT} --workers 3 --timeout 120 \
"
