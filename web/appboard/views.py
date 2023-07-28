import json

from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

from . import models
from . import forms

User = get_user_model()


@login_required
def home(request):
    return render(request, 'appboard/home.html')
