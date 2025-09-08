from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib import messages as dj_messages
from django.views.decorators.http import require_http_methods
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as auth_login, authenticate

from .models import Message
from .openai_utility import complete_chat


@login_required
def home(request):
    return render(request, "home.html")


@login_required
@require_http_methods(["GET", "POST"])
def chat(request):
    # simple rate-limit: 1 message / 2 seconds
    last = request.session.get("last_post_ts")
    now = timezone.now().timestamp()
    if request.method == "POST" and last and (now - float(last)) < 2.0:
        dj_messages.warning(request, "You're sending messages too quickly. Please wait a moment.")
        return redirect("chat")

    if request.method == "POST":
        user_text = (request.POST.get("message") or "").strip()
        if not user_text:
            dj_messages.error(request, "Please enter a message.")
            return redirect("chat")

        # Save user message
        Message.objects.create(user=request.user, role="user", content=user_text)

        # Build conversation (keep last ~12 messages to reduce token usage)
        history = list(
            Message.objects.filter(user=request.user).order_by("-created_at")[:12]
        )
        history.reverse()  # oldest first
        messages_payload = [{"role": m.role, "content": m.content} for m in history]

        # Guardrail system prompt
        system_prompt = (
            "You are a supportive, non-clinical companion for U.S. veterans. "
            "Be empathetic and practical. Do not provide medical, legal, or financial advice. "
            "If crisis indicators appear (self-harm, harm to others), advise calling 988 (Press 1)."
        )
        messages_payload.insert(0, {"role": "system", "content": system_prompt})

        # Call LLM
        assistant_text = complete_chat(messages_payload)

        # Save assistant reply
        Message.objects.create(user=request.user, role="assistant", content=assistant_text)

        # update tiny rate-limit marker
        request.session["last_post_ts"] = str(now)

        return redirect("chat")

    # GET -> render chat history
    history = Message.objects.filter(user=request.user).order_by("created_at")
    return render(request, "chat.html", {"history": history})


def signup(request):
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # auto-login after creating the user
            raw_username = form.cleaned_data["username"]
            raw_password = form.cleaned_data["password1"]
            user = authenticate(request, username=raw_username, password=raw_password)
            if user:
                auth_login(request, user)
            return redirect("home")
    else:
        form = UserCreationForm()
    return render(request, "signup.html", {"form": form})
