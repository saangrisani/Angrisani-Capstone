from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as auth_login
from django.shortcuts import render, redirect
from django.contrib import messages as dj_messages
from django.views.decorators.http import require_http_methods

#from .models import Message
from .openai_utility import complete_chat



def home(request):
    return render(request, "home.html")


@login_required
@require_http_methods(["GET", "POST"])
def chat(request):
    reply = None
    if request.method == "POST":
        return render(request, "chat.html", {"reply": None})
    user_text = (request.POST.get("message") or request.POST.get("text") or "").strip()    

    if not user_text:
            dj_messages.error(request, "Please tell me what I can help with today to serve your mental health needs.")
            return redirect("chat")
    payload = [
        {
        "role": "system",
        "content": (
            "You are a supportive, non-clinical and non medical mental health companion for U.S. military veterans."
            "Be empathetic and practical. Do not provide medical, legal, or financial advice."
            "If the user is in crisis, or the following crisis indicators appear(self-harm, harm to others, suicide ideations), advise veteran to call 988(Press option 1)."
            ),
        },
        {"role": "user", "content": user_text},
    ]
    reply = complete_chat(payload)
    return render(request, "chat.html", {"reply": reply})    

# about page
def about(request):
    return render(request, "app1/about.html")

#resources page
def resources(request):
    return render(request, "app1/resources.html")


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
