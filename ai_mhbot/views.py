# ai_mhbot/views.py
import math
import requests

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login
from django.shortcuts import render, redirect
from django.contrib import messages as dj_messages
from django.views.decorators.http import require_http_methods, require_GET
from django.http import JsonResponse

from .openai_utility import complete_chat

# custom form
from django.contrib.auth.forms import CustomUserCreationForm, CustomUserCreationForm
# ------------------------- Guardrails: system role + few-shots -------------------------
SYSTEM_ROLE = """You are a supportive, non-clinical mental health companion for U.S. military veterans and their families.

Core rules:
- Be empathetic, practical, and brief. Normalize seeking help.
- Offer general well-being ideas only (grounding, sleep hygiene, stress management, self-care planning).
- Do NOT provide medical advice, diagnoses, treatment plans, or instructions to start/stop/change medications.
- Do NOT recommend specific medications or interpret symptoms.
- Prefer resources: VA Mental Health, Vet Centers, crisis options (988 press 1).
- If there is self-harm/violence risk, do not continue a normal chat; give crisis options (988 press 1, text 838255, veteranscrisisline.net) and encourage emergency services if in immediate danger.
- Avoid collecting sensitive personal information. If users share it, do not repeat it back.
"""

FEW_SHOTS = [
    {"role": "user", "content": "I feel keyed up lately and can’t sleep. Any tips?"},
    {"role": "assistant", "content": "That’s really tough—thanks for sharing. Try a slow 4-4-6 breathing cycle for a couple minutes, dim screens an hour before bed, and keep your room cool and dark. If you wake, avoid the clock and do a brief body scan. I can also point you to VA sleep resources or help find a clinic nearby."},
    {"role": "user", "content": "Should I start Zoloft?"},
    {"role": "assistant", "content": "I can’t provide medical advice or recommend medications. A clinician can help you decide. If you’d like, I can share general coping ideas and help you find a provider or Vet Center."},
]

# ------------------------- Public pages -------------------------
def home(request):
    return render(request, "app1/home.html")

def about(request):
    return render(request, "app1/about.html")

def resources(request):
    return render(request, "app1/resources.html")

def feedback(request):
    return render(request, "app1/feedback.html")

def exercise_breathing(request):
    return render(request, "app1/exercise_breathing.html")

def exercise_grounding(request):
    return render(request, "app1/exercise_grounding.html")

def exercise_sleep(request):
    return render(request, "app1/exercise_sleep.html")

# -------------------------- Auth / account pages --------------------------
def signup(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            dj_messages.success(request, "Welcome! Your account was created successfully.")
            return redirect("home")
    else:
        form = CustomUserCreationForm()
    return render(request, "app1/signup.html", {"form": form})

@login_required
def profile(request):
    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            dj_messages.success(request, "Profile updated successfully.")
            return redirect("profile")
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, "app1/profile.html")

@require_http_methods(["GET", "POST"])
@login_required
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

    payload = [{"role": "system", "content": SYSTEM_ROLE}] + FEW_SHOTS + [
        {"role": "user", "content": user_text}
    ]

    try:
        raw = complete_chat(payload)
        reply = None
        if raw is None:
            reply = None
        elif isinstance(raw, str):
            reply = raw
        elif isinstance(raw, dict):
            reply = (
                raw.get("content")
                or raw.get("message", {}).get("content")
                or raw.get("choices", [{}])[0].get("message", {}).get("content")
                or raw.get("choices", [{}])[0].get("delta", {}).get("content")
            )
        elif isinstance(raw, (list, tuple)):
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


