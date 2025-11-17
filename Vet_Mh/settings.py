"""
Django settings for Vet_Mh.

This file was reviewed and simplified with help from ChatGPT (GPT-5).
- Removes duplicates (ALLOWED_HOSTS defined once)
- Keeps local .env loading for dev, but uses real env in prod (Cloud Run)
- Readies static files for WhiteNoise in production
- Places optional django-axes correctly
"""

from pathlib import Path
import os

# ──────────────────────────────────────────────────────────────────────────────
# Paths & Environment
# ──────────────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env only in local/dev environments:
# In Cloud Run, use env vars / Secret Manager (do not rely on .env).
if os.getenv("LOAD_DOTENV", "true").lower() == "true":
    try:
        from dotenv import load_dotenv, find_dotenv  # type: ignore
        _found = find_dotenv(filename=".env", usecwd=True)
        load_dotenv(_found or (BASE_DIR / ".env"))
    except Exception:
        # Safe no-op if python-dotenv isn't installed in prod images
        pass

# ──────────────────────────────────────────────────────────────────────────────
# Core toggles
# ──────────────────────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret-key")  # override in prod
DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() == "true"

# Accept space- or comma-separated host list from env; default to localhost + Codespaces
_default_hosts = (
    "localhost 127.0.0.1 "
    "reimagined-potato-v6vw9xrgjj9v2w4w5-8000.app.github.dev"
)
_allowed_raw = os.getenv("DJANGO_ALLOWED_HOSTS", _default_hosts)
ALLOWED_HOSTS = [h for h in _allowed_raw.replace(",", " ").split() if h]

# CSRF trusted origins: env override, with sane local defaults
_default_csrf = (
    "http://127.0.0.1:8000 "
    "http://localhost:8000 "
    "https://127.0.0.1:8000 "
    "https://localhost:8000 "
    "https://localhost:8080 "
    "https://localhost:8090 "
    "https://reimagined-potato-v6vw9xrgjj9v2w4w5-8000.app.github.dev"
)
_csrf_raw = os.getenv("CSRF_TRUSTED_ORIGINS", _default_csrf)
CSRF_TRUSTED_ORIGINS = [o for o in _csrf_raw.replace(",", " ").split() if o]

# If behind a proxy (Cloud Run, Nginx), trust forwarded proto for secure redirects
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ──────────────────────────────────────────────────────────────────────────────
# Installed apps
# ──────────────────────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    # Order matters: whitenoise shim prevents Django from serving static in dev
    "whitenoise.runserver_nostatic",

    # Django apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Your app (use the AppConfig path; do NOT also add plain "ai_mhbot")
    "ai_mhbot.apps.AiMhbotConfig",

    # Optional: brute-force defense + audit (pip install django-axes)
    # Enable only if you've installed it:
    # "axes",
]

# ──────────────────────────────────────────────────────────────────────────────
# Middleware
# ──────────────────────────────────────────────────────────────────────────────
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",

    # WhiteNoise must be directly after SecurityMiddleware
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",

    # If you enable django-axes, uncomment this (and add "axes" to INSTALLED_APPS)
    # "axes.middleware.AxesMiddleware",

    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ──────────────────────────────────────────────────────────────────────────────
# URLs / WSGI / ASGI
# ──────────────────────────────────────────────────────────────────────────────
ROOT_URLCONF = "Vet_Mh.urls"
WSGI_APPLICATION = "Vet_Mh.wsgi.application"
# (Keep asgi.py too, for future async; no setting needed here)

# ──────────────────────────────────────────────────────────────────────────────
# Templates
# ──────────────────────────────────────────────────────────────────────────────
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # Your repo has /templates and app templates; APP_DIRS=True auto-discovers
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

# ──────────────────────────────────────────────────────────────────────────────
# Database (SQLite for dev/demo; move to Cloud SQL for prod)
# ──────────────────────────────────────────────────────────────────────────────
DATABASES = {
    "default": {
        "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.getenv("DB_NAME", BASE_DIR / "db.sqlite3"),
        # For Postgres example in prod:
        # "ENGINE": "django.db.backends.postgresql",
        # "NAME": os.getenv("DB_NAME"),
        # "USER": os.getenv("DB_USER"),
        # "PASSWORD": os.getenv("DB_PASSWORD"),
        # "HOST": os.getenv("DB_HOST"),
        # "PORT": os.getenv("DB_PORT", "5432"),
    }
}

# ──────────────────────────────────────────────────────────────────────────────
# Auth / i18n
# ──────────────────────────────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "America/Los_Angeles"
USE_I18N = True
USE_TZ = True

# ──────────────────────────────────────────────────────────────────────────────
# Static files (author in /static; collect to /staticfiles)
# ──────────────────────────────────────────────────────────────────────────────
# Use path-style STATIC_URL (no leading slash) for modern Django
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]      # your authored assets
STATIC_ROOT = BASE_DIR / "staticfiles"        # collectstatic output

# Storage: simple in dev; compressed manifest in prod for far-future caching
if DEBUG:
    STORAGES = {
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        }
    }
else:
    STORAGES = {
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
        }
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ──────────────────────────────────────────────────────────────────────────────
# Auth redirects
# ──────────────────────────────────────────────────────────────────────────────
LOGIN_REDIRECT_URL = "/chat/"
LOGOUT_REDIRECT_URL = "/"
LOGIN_URL = "/login/"

# ──────────────────────────────────────────────────────────────────────────────
# Security toggles (tighten in prod)
# ──────────────────────────────────────────────────────────────────────────────
SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

# ──────────────────────────────────────────────────────────────────────────────
# Third-party / API keys (kept here for convenience; read from env)
# ──────────────────────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")

# Optional django-axes defaults (only effective if "axes" installed & middleware enabled)
AXES_ENABLED = os.getenv("AXES_ENABLED", "false").lower() == "true"
AXES_FAILURE_LIMIT = int(os.getenv("AXES_FAILURE_LIMIT", "5"))
AXES_COOLOFF_TIME = int(os.getenv("AXES_COOLOFF_TIME", "60"))  # minutes
