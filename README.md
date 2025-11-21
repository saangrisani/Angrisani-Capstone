Veterans Mental Health Companion - Project Readme
Live Production Site:
https://vetmh-app-1007759072149.us-central1.run.app
Quickstart - Local Development
1. Clone Repository:
git clone && cd Angrisani-Capstone
2. Create .env file:
Add your environment variables, including DJANGO settings and API keys.
3. Run App Locally:
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
4. Create Admin Superuser:
python manage.py createsuperuser
Access the admin at http://127.0.0.1:8000/admin/
5. Docker Support:
docker build -t capstone:local .
docker run --rm --name capstone -p 8090:8080 --env-file .env capstone:local
6. Production Deployment:
Deployed on Google Cloud Run with environment variables configured for Django, OpenAI, and Google
Maps integration.
