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


4) Docker run

docker build -t capstone:local .
docker run --rm --name capstone \
  -p 8090:8080 \
  --env-file .env \
  -e DJANGO_ALLOWED_HOSTS="localhost,127.0.0.1" \
  -e CSRF_TRUSTED_ORIGINS="http://localhost:8090 https://localhost:8090 http://127.0.0.1:8090 https://127.0.0.1:8090" \
  capstone:local
# open http://localhost:8090