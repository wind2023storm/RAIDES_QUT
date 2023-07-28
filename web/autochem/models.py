import os
import uuid

from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model
import django.core.validators as validators
from django.conf import settings

User = get_user_model()
