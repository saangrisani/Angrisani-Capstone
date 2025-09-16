from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as auth_login
from django.shortcuts import render, redirect
from django.contrib import messages as dj_messages
from django.views.decorators.http import require_http_methods

#from .models import Message
from .openai_utility import complete_chat


# -------------------------public pages ------------------------
def home(request):
    return render(request, "app1/home.html")
# about page
def about(request):
    return render(request, "app1/about.html")
#resources page
def resources(request):
    return render(request, "app1/resources.html")

# -------------------------- authorized / account pages ---------------------------
@login_required
# Sign up 
def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            dj_messages.success(request, "Welcome! Your account was created successfully.")
            return redirect("home")
    else:
        form = UserCreationForm()
    return render(request, "signup.html", {"form": form})


@require_http_methods(["GET", "POST"])
def chat(request):
    if request.method == "GET":
        return render(request, "app1/chat.html")

    # Accept several input names: message, text, prompt, content
    for key in ("message", "text", "prompt", "content"):
        user_text = request.POST.get(key)
        if user_text:
            user_text = user_text.strip()
            break
    else:
        user_text = ""

    if not user_text:
        dj_messages.error(request, "Please tell me what I can help with today to serve your mental health needs.")
        return render(request, "app1/chat.html", {"reply": None})

    payload = [
        {
            "role": "system",
            "content": (
                "You are a supportive, non-clinical and non medical mental health companion "
                "for U.S. military veterans. Be empathetic and practical. Do not provide "
                "medical, legal, or financial advice. If the user is in crisis (self-harm, "
                "harm to others, suicide ideations), advise calling 988 (press 1)."
            ),
        },
        {"role": "user", "content": user_text},
    ]

    try:
        raw = complete_chat(payload)

        # Coerce common return shapes -> string
        reply = None
        if raw is None:
            reply = None
        elif isinstance(raw, str):
            reply = raw
        elif isinstance(raw, dict):
            # Try a few common keys/paths
            reply = (
                raw.get("content")
                or raw.get("message", {}).get("content")
                or raw.get("choices", [{}])[0].get("message", {}).get("content")
                or raw.get("choices", [{}])[0].get("delta", {}).get("content")
            )
        elif isinstance(raw, (list, tuple)):
            # e.g., [{"role":"assistant","content":"..."}]
            for item in raw:
                if isinstance(item, dict) and item.get("role") == "assistant" and item.get("content"):
                    reply = item["content"]
                    break

        if not reply:
            dj_messages.warning(request, "I didn’t get a usable response from the chat backend.")
            reply = None

    except Exception as e:
        dj_messages.error(request, f"Chat backend error: {e}")
        reply = None

    return render(request, "app1/chat.html", {"reply": reply, "user_text": user_text})



