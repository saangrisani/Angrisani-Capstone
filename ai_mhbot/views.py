# ai_mhbot/views.py
import math
import requests
import os, re

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login
from django.shortcuts import render, redirect
from django.contrib import messages as dj_messages
from django.views.decorators.http import require_http_methods, require_GET
from django.http import JsonResponse

from .openai_utility import complete_chat

# custom form
from .forms import CustomUserCreationForm, UserProfileForm
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

    return render(request, "app1/profile.html", {"form": form})

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

    # -------------------------- Veterans Nearby feature --------------------------
    # --- VA Finder: Google Places (Text Search New) ---


VET_REGEX = re.compile(
    r'\b(va|veterans?|vet\s*center|department of veterans affairs|county veterans service|vfw|american legion|dav|amvets|us\s*vets)\b',
    re.I
)

def _filter_veteran_places(places):
    out = []
    for p in places or []:
        name = (p.get("displayName", {}) or {}).get("text", "") or ""
        addr = p.get("formattedAddress", "") or ""
        if VET_REGEX.search(f"{name} {addr}"):
            out.append(p)
    return out

@require_GET
def veterans_nearby(request):
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return JsonResponse({"results": [], "error": "Missing GOOGLE_MAPS_API_KEY"}, status=500)

    place_str = (request.GET.get("place") or "").strip()
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")
    radius_m = int(request.GET.get("radius", "20000"))

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": (
            "places.id,places.displayName,places.formattedAddress,places.types,"
            "places.location,places.nationalPhoneNumber,places.internationalPhoneNumber,"
            "places.websiteUri,places.googleMapsUri"
        ),
    }

    # --- A) If a city/state or ZIP was provided, run a Text Search anchored to that phrase.
    if place_str:
        body = {
            "textQuery": f'(VA OR Veterans OR "Vet Center" OR "American Legion" OR VFW OR DAV) in {place_str}',
            "pageSize": 20,
            # No locationBias when textQuery includes an explicit location phrase.
        }
        r = requests.post("https://places.googleapis.com/v1/places:searchText",
                          json=body, headers=headers, timeout=20)
        if not r.ok:
            return JsonResponse({"results": [], "error": f"TextSearch {r.status_code}", "details": r.text}, status=502)
        data = r.json()
        return JsonResponse({"results": _filter_veteran_places(data.get("places"))})

    # --- B) Otherwise, try Text Search with a location bias (lat/lng path).
    try:
        lat_f = float(lat or "0")
        lng_f = float(lng or "0")
    except ValueError:
        return JsonResponse({"results": [], "error": "Invalid lat/lng"}, status=400)

    text_body = {
        "textQuery": 'VA OR Veterans OR "Vet Center" OR "American Legion" OR VFW OR DAV',
        "locationBias": {"circle": {"center": {"latitude": lat_f, "longitude": lng_f}, "radius": radius_m}},
        "pageSize": 20,
    }
    t = requests.post("https://places.googleapis.com/v1/places:searchText",
                      json=text_body, headers=headers, timeout=20)
    if not t.ok:
        return JsonResponse({"results": [], "error": f"TextSearch {t.status_code}", "details": t.text}, status=502)
    t_data = t.json()
    t_filtered = _filter_veteran_places(t_data.get("places"))
    if t_filtered:
        return JsonResponse({"results": t_filtered})

    # Optional Nearby fallback if Text Search came up empty
    nearby_body = {
        "includedTypes": ["hospital","doctor","physiotherapist","local_government_office","point_of_interest"],
        "maxResultCount": 20,
        "locationRestriction": {"circle": {"center": {"latitude": lat_f, "longitude": lng_f}, "radius": radius_m}},
    }
    n = requests.post("https://places.googleapis.com/v1/places:searchNearby",
                      json=nearby_body, headers=headers, timeout=20)
    if not n.ok:
        return JsonResponse({"results": [], "error": f"NearbySearch {n.status_code}", "details": n.text}, status=502)
    return JsonResponse({"results": _filter_veteran_places(n.json().get("places"))})


