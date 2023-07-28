import os

from django.urls import path, re_path, include
from django.conf import settings
from . import views

app_name = 'forum'

urlpatterns = [
    path('', views.home, name='home'),
]
