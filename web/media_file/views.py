import json

from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

from .models import MediaFile
from . import forms

User = get_user_model()
