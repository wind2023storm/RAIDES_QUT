import json

from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

from . import models
from . import forms

User = get_user_model()


def home(request):
    return HttpResponse("App Homepage")