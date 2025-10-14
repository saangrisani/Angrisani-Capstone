#----------------------------------------------------------------------------------
#  ai_mhbot/views.py
# Purpose of file: my django views here for chat, and for veteran resources
# This is used by the urls.py which calls these, and templates render results
import os, re, math, requests
from openai import OpenAI
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login
from django.shortcuts import render, redirect
from django.contrib import messages as dj_messages
from django.views.decorators.http import require_http_methods, require_GET
from django.http import JsonResponse

from .openai_utility import complete_chat
from .forms import CustomUserCreationForm, UserProfileForm

# ------------------------- Guardrails: system role + few-shots -------------------------
# I keep the system role and few-shots here at the top so they're quick and easy to update(I plan to adapt more)
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
# so these are here as examples of what a veteranmight say, and how this bot should also respond, it is very simplistic
# as of now, but I plan to make it more robust as I continue development.
FEW_SHOTS = [
    {"role": "user", "content": "I feel keyed up lately and can’t sleep. Any tips?"},
    {"role": "assistant", "content": "That’s really tough—thanks for sharing. Try a slow 4-4-6 breathing cycle for a couple minutes, dim screens an hour before bed, and keep your room cool and dark. If you wake, avoid the clock and do a brief body scan. I can also point you to VA sleep resources or help find a clinic nearby."},
    {"role": "user", "content": "Should I start Zoloft?"},
    {"role": "assistant", "content": "I can’t provide medical advice or recommend medications. A clinician can help you decide. If you’d like, I can share general coping ideas and help you find a provider or Vet Center."},
]

# ------------------------- Public pages -------------------------
def home(request): return render(request, "app1/home.html")
def about(request): return render(request, "app1/about.html")
def resources(request): return render(request, "app1/resources.html")
def feedback(request): return render(request, "app1/feedback.html")
def exercise_breathing(request): return render(request, "app1/exercise_breathing.html")
def exercise_grounding(request): return render(request, "app1/exercise_grounding.html")
def exercise_sleep(request): return render(request, "app1/exercise_sleep.html")

# -------------------------- Auth / account pages --------------------------
# Sign-up -> Create User -> Automatic Login -> Redirect to Home. Has user friendly messages along the way.
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

# Profile, required to have a log in to access.
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
    return render(request, "app1/profile.html", {"form": form})

# Chat view: GET shows chat page, POST processes input and shows reply
@require_http_methods(["GET", "POST"])
@login_required
def chat(request):
    if request.method == "GET":
        return render(request, "app1/chat.html")

    # Accept several possible input field names for flexibility and so it doesn't break easily
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
# payload is built here with system role, few-shots, and user input
    payload = [{"role": "system", "content": SYSTEM_ROLE}] + FEW_SHOTS + [{"role": "user", "content": user_text}]
# call complete_chat to get a response from the chat backend
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

# -------------------------- Veterans Nearby (Google Places Text Search New) --------------------------
# I scan for veteran resources so I don't toss irrelevant places back to the user
VET_REGEX = re.compile(
    r'\b(va|veterans?|vet\s*center|department of veterans affairs|county veterans service|vfw|american legion|dav|amvets|us\s*vets)\b',
    re.I
)
# filter function to keep only veteran-related places from Google Places results API
def _filter_veteran_places(places):
    out = []
    for p in places or []:
        name = (p.get("displayName", {}) or {}).get("text", "") or ""
        addr = p.get("formattedAddress", "") or ""
        if VET_REGEX.search(f"{name} {addr}"):
            out.append(p)
    return out

# GET endpoint to find nearby veteran resources using Google Places API
# Accepts either 'place' (text location) or 'lat' and 'lng'
# fixed using CHatGPT to use the new Google Places Text Search API
@require_GET
def veterans_nearby(request):
    """
    What: find veteran-related places by city/state (?place=Chico, CA)
    Why: simplest UX—users think in city/state, not coords.
    Returns: JSON {results: [...], error?: str}
    """
    api_key = settings.GOOGLE_MAPS_API_KEY or os.getenv("GOOGLE_MAPS_API_KEY", "")
    if not api_key:
        return JsonResponse({"results": [], "error": "Missing GOOGLE_MAPS_API_KEY"}, status=200)

    place = (request.GET.get("place") or "").strip()
    if not place:
        return JsonResponse({"results": [], "error": "Provide ?place=City, State"}, status=200)

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": (
            "places.id,places.displayName,places.formattedAddress,places.types,"
            "places.location,places.nationalPhoneNumber,places.internationalPhoneNumber,"
            "places.websiteUri,places.googleMapsUri"
        ),
    }
    body = {"textQuery": f'(VA OR Veterans OR "Vet Center" OR "American Legion" OR VFW OR DAV) in {place}', "pageSize": 20}

    try:
        r = requests.post("https://places.googleapis.com/v1/places:searchText",
                          json=body, headers=headers, timeout=15)
        if not r.ok:
            return JsonResponse({"results": [], "error": f"TextSearch {r.status_code}", "details": r.text}, status=200)
        return JsonResponse({"results": _filter_veteran_places(r.json().get("places"))}, status=200)
    except requests.Timeout:
        return JsonResponse({"results": [], "error": "Upstream timeout"}, status=200)
    except requests.RequestException as e:
        return JsonResponse({"results": [], "error": "Upstream request failed", "details": str(e)}, status=200)