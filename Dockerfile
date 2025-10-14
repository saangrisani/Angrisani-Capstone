FROM python:3.12.6-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080

# HTTPS certs for OpenAI, curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install deps first for better caching
COPY requirements.txt /app/
RUN python -m pip install --upgrade pip \
 && pip install -r requirements.txt

# App code + entry script
COPY . /app/
RUN chmod +x /app/docker_run_server.sh

# Expose the internal port; you can map it to 80 on run if you want
EXPOSE 8080

ENTRYPOINT ["/app/docker_run_server.sh"]
