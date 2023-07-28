import os
import uuid

from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model
import django.core.validators as validators
from django.conf import settings
# from django.utils.translation import ugettext_lazy as _

User = get_user_model()

class UploadDataTypeChoices(models.TextChoices):
    ROCK = 'ROCK', ('Rock Chip')
    SOIL = 'SOIL', ('Drilling Soils')
    SEDI = 'SEDI', ('Sediments')
