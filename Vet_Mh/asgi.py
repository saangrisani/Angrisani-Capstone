"""
ASGI config for Vet_Mh project.

It exposes the ASGI callable as a module-level variable named ``application``.

This file was cleaned and restored with help from ChatGPT (GPT-5)
to ensure proper async compatibility and project readiness.

For more information, see:
https://docs.djangoproject.com/en/stable/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Vet_Mh.settings')

application = get_asgi_application()
