# Dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN python -m pip install --upgrade pip && pip install -r requirements.txt

COPY . /app/

EXPOSE 8000
CMD ["bash", "-lc", "python manage.py migrate && \
  python manage.py collectstatic --noinput || true && \
  gunicorn Vet_Mh.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3 --timeout 120"]
