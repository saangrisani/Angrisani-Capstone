Quickstart

1) Clone

git clone <repo-url> && cd Angrisani-Capstone


2) Create .env (no quotes)

DJANGO_SETTINGS_MODULE=Vet_Mh.settings
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:8000 http://127.0.0.1:8000

OPENAI_API_KEY=sk-XXXXXXXX
OPENAI_MODEL=chatgpt-4o-latest
GOOGLE_MAPS_API_KEY=AIzaSyXXXXXXXX


3) Local run

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
# open http://127.0.0.1:8000

5) Create a Django superuser (admin)

If you want to inspect site data in Django's admin dashboard, create a superuser:

# run migrations first if you haven't already
python manage.py migrate

# create a superuser and follow the prompts (email optional)
python manage.py createsuperuser
```

Then start the server and visit the admin site:

python manage.py runserver
# open http://127.0.0.1:8000/admin/ in browser


6) Log in and review the Admin dashboard

- Use the superuser credentials you created to sign in at `/admin/`.
- Recommended places to review:
  - Users: inspect `auth > Users` to see registered accounts.
  - Profiles: view `ai_mhbot > Profile` to check stored phone/email fields.
  - Chat messages: `ai_mhbot > ChatMessage` to review user/assistant messages and `meta` JSON.
  - Mood entries: `ai_mhbot > MoodEntry` to view daily mood logs and notes.
  - Login events: `ai_mhbot > LoginEvent` for signup/login auditing.

Notes:
- If you don't see some models in the admin, they may not be registered; check `ai_mhbot/admin.py`.

4) Docker run

docker build -t capstone:local .
docker run --rm --name capstone \
  -p 8090:8080 \
  --env-file .env \
  -e DJANGO_ALLOWED_HOSTS="localhost,127.0.0.1" \
  -e CSRF_TRUSTED_ORIGINS="http://localhost:8090 https://localhost:8090 http://127.0.0.1:8090 https://127.0.0.1:8090" \
  capstone:local
# open http://localhost:8090