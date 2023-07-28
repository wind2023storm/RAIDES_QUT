from django import forms
from django.db import models
from django.db.models import Q
from .models import Task
from django.contrib.auth import get_user_model


class CreateTaskForm(forms.ModelForm):

    class Meta:
        model = Task
        exclude = ('',)
