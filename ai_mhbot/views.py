
# Purpose: Django views for chat, veterans resources, auth pages, mood tracker, and profile.

import os, re, requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login
from django.shortcuts import render, redirect
from django.contrib import messages as dj_messages
from django.views.decorators.http import require_http_methods, require_GET
from django.http import JsonResponse
# ChatGPT assist 2025-10-31: import the profile update forms
from .forms import CustomUserCreationForm, ProfileUpdateForm, UserUpdateForm
from .models import MoodEntry, Profile, ChatMessage
from .openai_utility import complete_chat

# ------------------------- Guardrails: system role + few-shots -------------------------
SYSTEM_ROLE = """You are a supportive, non-clinical mental health companion for U.S. military veterans and their families. For all other questions, politely state that the question is outside your scope and suggest they consult a relevant professional. You should not answer questions outside your scope. You should not provide medical advice, diagnoses, treatment plans, or instructions to start/stop/change medications. You should not recommend specific medications or interpret symptoms.

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
def home(request): return render(request, "app1/home.html")
def about(request): return render(request, "app1/about.html")
def resources(request): return render(request, "app1/resources.html")
def feedback(request): return render(request, "app1/feedback.html")
def exercise_breathing(request): return render(request, "app1/exercise_breathing.html")
def exercise_grounding(request): return render(request, "app1/exercise_grounding.html")
def exercise_sleep(request): return render(request, "app1/exercise_sleep.html")

# -------------------------- Auth / account pages --------------------------
def signup(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # first_name, last_name, email all set in form.save()
            dj_messages.success(
                request,
                "Account created. Please sign in to continue."
            )
            return redirect("login")  # <-- redirect to login after signup
        # fall through to re-render with errors
    else:
        form = CustomUserCreationForm()

    return render(request, "app1/signup.html", {"form": form})

@login_required
def profile(request):
    prof, _ = Profile.objects.get_or_create(user=request.user)

    # ChatGPT assist 2025-10-31: support read-only + ?edit=1 toggle
    editing = request.GET.get("edit") == "1"

    if request.method == "POST":
        # we only save when editing
        uform = UserUpdateForm(request.POST, instance=request.user)
        pform = ProfileUpdateForm(request.POST, instance=prof)
        if uform.is_valid() and pform.is_valid():
            uform.save()
            pform.save()
            dj_messages.success(request, "Profile updated.")
            return redirect("profile")  # go back to read-only
        # if invalid, stay in editing mode
        return render(
            request,
            "app1/profile.html",
            {
                "editing": True,
                "profile": prof,
                "uform": uform,
                "pform": pform,
            },
        )

    # GET
    uform = UserUpdateForm(instance=request.user)
    pform = ProfileUpdateForm(instance=prof)
    return render(
        request,
        "app1/profile.html",
        {
            "editing": editing,
            "profile": prof,
            "uform": uform,
            "pform": pform,
        },
    )

# -------------------------- Chat --------------------------
@require_http_methods(["GET", "POST"])
@login_required
def chat(request):
    if request.method == "GET":
        return render(request, "app1/chat.html")

    # 1) get user text
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

    session_key = request.session.session_key or f"user-{request.user.id}"

    # 2) save user chat message
    ChatMessage.objects.create(
        user=request.user,
        session_id=session_key,
        role="user",
        content=user_text,
    )

    # 3) detect mood but DON'T save yet
    lowered = user_text.lower()
    pending_mood = None  # will be ("anxious", "detected anxious wording in chat")
    if any(w in lowered for w in ["suicid", "kill myself", "end it", "can't go on"]):
        pending_mood = ("stressed", "flagged crisis language in chat")
    elif any(w in lowered for w in ["panic", "panicking", "anxious", "anxiety", "overwhelmed"]):
        pending_mood = ("anxious", "detected anxious wording in chat")
    elif any(w in lowered for w in ["angry", "mad", "pissed", "frustrated"]):
        pending_mood = ("angry", "detected anger/frustration in chat")
    elif any(w in lowered for w in ["sad", "down", "depressed", "lonely"]):
        pending_mood = ("down", "detected low/sad wording in chat")
    elif any(w in lowered for w in ["tired", "stressed", "burned out", "burnt out", "exhausted"]):
        pending_mood = ("stressed", "detected stress/fatigue in chat")
    elif any(w in lowered for w in ["ok", "fine", "alright", "hanging in"]):
        pending_mood = ("ok", "neutral wording in chat")
    elif any(w in lowered for w in ["good", "great", "better today", "feeling better"]):
        pending_mood = ("good", "positive wording in chat")

    # 4) call OpenAI
    payload = [{"role": "system", "content": SYSTEM_ROLE}] + FEW_SHOTS + [{"role": "user", "content": user_text}]
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

    # 5) save assistant message
    ChatMessage.objects.create(
        user=request.user,
        session_id=session_key,
        role="assistant",
        content=reply or "",
        meta={"source": "openai", "ok": bool(reply)},
    )

    # 6) NOW save mood with full chat context
    if pending_mood:
        mood_val, note_txt = pending_mood
        MoodEntry.objects.create(
            user=request.user,
            mood=mood_val,
            note=note_txt,
            chat_user_text=user_text,
            chat_assistant_text=reply or "",
        )

    return render(request, "app1/chat.html", {"reply": reply, "user_text": user_text})
# -------------------------- Mood Tracker --------------------------
@login_required
def mood_add(request):
    if request.method == "POST":
        mood = request.POST.get("mood", "ok")
        note = request.POST.get("note", "")
        MoodEntry.objects.create(user=request.user, mood=mood, note=note)
    return redirect("mood_dashboard")

@login_required
def mood_dashboard(request):
    entries = list(MoodEntry.objects.filter(user=request.user).order_by("created_at"))
    mood_order = ["great","good","ok","sad","down","angry","anxious","stressed"]
    idx = {m: i for i, m in enumerate(mood_order)}
    labels = [e.created_at.strftime("%b %d") for e in entries]
    values = [idx.get(e.mood, 0) for e in entries]
    return render(request, "mood/dashboard.html", {"entries": entries, "labels": labels, "values": values})

# -------------------------- Veterans Nearby (Google Places Text Search) --------------------------
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
    """
    Find veteran-related places by city/state (?place=Chico, CA)
    Returns JSON {results: [...], error?: str}
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
        r = requests.post("https://places.googleapis.com/v1/places:searchText", json=body, headers=headers, timeout=15)
        if not r.ok:
            return JsonResponse({"results": [], "error": f"TextSearch {r.status_code}", "details": r.text}, status=200)
        return JsonResponse({"results": _filter_veteran_places(r.json().get("places"))}, status=200)
    except requests.Timeout:
        return JsonResponse({"results": [], "error": "Upstream timeout"}, status=200)
    except requests.RequestException as e:
        return JsonResponse({"results": [], "error": "Upstream request failed", "details": str(e)}, status=200)
