from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model

import requests
from projects.models import Project
from . import models


UserModel = get_user_model()


@receiver(post_save, sender=UserModel)
def create_user_management(sender, instance, created, **kwargs):
    print("OK")
    if created:
        r = requests.request("POST", "http://localhost:9000/api/v1/auth/register", 
        json={"accepted_terms":"True", "email": instance.email, "full_name": instance.first_name + ' ' + instance.last_name, "password": instance.password, "type":"public", "username": instance.email}, 
        headers={"Content-Type": "application/json"})
