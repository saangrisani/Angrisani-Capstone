from django.shortcuts import render
from .openai_utility import get_openai_response
# Create your views here.
from django.contrib.auth.decorators import login_required
@login_required
def home(request):
    return render(request, "home.html")

@login_required
def chat(request):
    #week 3 stuff
    return render(request, "chat.html")