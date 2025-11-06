"""
Login/Logout auditing signals for ai_mhbot.

Created with help from ChatGPT (GPT-5).
- Hooks Django's built-in auth signals to record: success, failure, logout
- Captures client IP using django-ipware (best-effort behind proxies)
- Stores User-Agent for basic device/browser context

Docs:
- Django auth signals: https://docs.djangoproject.com/en/stable/ref/contrib/auth/#signals
- django-ipware: https://pypi.org/project/django-ipware/
"""

from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from ipware import get_client_ip

from .models import LoginEvent  # ensure this model exists (see previous step)

User = get_user_model()

def _extract_ip_ua(request):
    """
    Safely extract client IP and User-Agent string.
    ipware.get_client_ip returns (ip, is_routable).
    If behind proxies (Cloud Run, Nginx), make sure SECURE_PROXY_SSL_HEADER is set in settings.
    """
    ip, _is_routable = (None, False)
    ua = ""
    if request is not None:
        ip, _is_routable = get_client_ip(request)  # may return None
        ua = request.META.get("HTTP_USER_AGENT", "")
    return ip, ua

@receiver(user_logged_in)
def on_user_logged_in(sender, request, user, **kwargs):
    """
    Fires after a successful login.
    """
    ip, ua = _extract_ip_ua(request)
    LoginEvent.objects.create(
        user=user,
        event="login_success",
        ip_address=ip,
        user_agent=ua,
    )

@receiver(user_logged_out)
def on_user_logged_out(sender, request, user, **kwargs):
    """
    Fires on logout.
    """
    ip, ua = _extract_ip_ua(request)
    # user may be None in some flows; LoginEvent allows null user
    LoginEvent.objects.create(
        user=user if isinstance(user, User) else None,
        event="logout",
        ip_address=ip,
        user_agent=ua,
    )

@receiver(user_login_failed)
def on_user_login_failed(sender, credentials, request, **kwargs):
    """
    Fires when authentication fails.
    credentials may include 'username' (string). Do NOT store raw password.
    """
    ip, ua = _extract_ip_ua(request)
    username = ""
    try:
        username = (credentials or {}).get("username", "") or ""
    except Exception:
        pass

    LoginEvent.objects.create(
        user=None,
        event="login_failed",
        username_tried=username[:150],  # avoid overlength
        ip_address=ip,
        user_agent=ua,
    )
