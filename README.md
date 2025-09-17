# Angrisani-Capstone
repo for my capstone design for 2025 fall with Matt Hill
## What’s Implemented
- Django project `Vet_Mh` with app `ai_mhbot`
- Pages: Home, Chat, About, Resources; auth (login/signup/logout)
- Shared navbar include
- OpenAI chat helper (`ai_mhbot/openai_utility.py`) reading `OPENAI_API_KEY` /
`OPENAI_MODEL`
## Quickstart
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
## OpenAI Test
python manage.py shell -c "import os,django;
os.environ.setdefault('DJANGO_SETTINGS_MODULE','Vet_Mh.settings');
django.setup(); from ai_mhbot.openai_utility import complete_chat;
print(complete_chat([{'role':'user','content':'Say hi in one short sentence.'}],
model=os.getenv('OPENAI_MODEL')))"
## Env
- `OPENAI_API_KEY`, `OPENAI_MODEL`
- `SECRET_KEY`, `ALLOWED_HOSTS`
