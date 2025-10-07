import os, pathlib

ENV_PATH = pathlib.Path(".env")
if ENV_PATH.exists():
    print(".env already exists. Nothing to do.")
    raise SystemExit(0)

# Pull from existing environment (Codespaces/CI/your shell)
vars_needed = {
    "DJANGO_SETTINGS_MODULE": os.getenv("DJANGO_SETTINGS_MODULE", "Vet_Mh.settings"),
    "DJANGO_SECRET_KEY": os.getenv("DJANGO_SECRET_KEY", "change-me"),
    "DJANGO_DEBUG": os.getenv("DJANGO_DEBUG", "True"),
    "DJANGO_ALLOWED_HOSTS": os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1"),
    "CSRF_TRUSTED_ORIGINS": os.getenv("CSRF_TRUSTED_ORIGINS", "http://localhost:8000 http://127.0.0.1:8000"),
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
}

with ENV_PATH.open("w") as f:
    for k, v in vars_needed.items():
        f.write(f"{k}={v}\n")

print("Created .env from current environment. Update it if needed.")
