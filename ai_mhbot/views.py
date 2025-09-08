from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib import messages as dj_messages
from django.views.decorators.http import require_http_methods

from .models import Message
from .openai_utility import complete_chat

@login_required
def home(request):
    return render(request, "home.html")

@login_required
@require_http_methods(["GET", "POST"])
def chat(request):
    last = request.session.get("last_post_ts")
    now = timezone.now().timestamp()

    if request.method == "POST":
        if last and (now - float(last)) < 2.0:
            dj_messages.warning(request, "Please wait a moment before sending again.")
            return redirect("chat")

        text = (request.POST.get("message") or "").strip()
        if not text:
            dj_messages.error(request, "Please enter a message.")
            return redirect("chat")

        Message.objects.create(user=request.user, role="user", content=text)

        history = list(Message.objects.filter(user=request.user).order_by("-created_at")[:12])
        history.reverse()
        payload = [{"role": m.role, "content": m.content} for m in history]
        payload.insert(0, {"role": "system", "content": "Be supportive and non-clinical. Crisis? Advise 988 (Press 1)."})

        reply = complete_chat(payload)
        Message.objects.create(user=request.user, role="assistant", content=reply)

        request.session["last_post_ts"] = str(now)
        return redirect("chat")

    history = Message.objects.filter(user=request.user).order_by("created_at")
    return render(request, "chat.html", {"history": history})

# NEW minimal pages (no login needed)
def about(request):
    return render(request, "app1/about.html")

def resources(request):
    return render(request, "app1/resources.html")