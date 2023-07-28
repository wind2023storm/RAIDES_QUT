from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.utils import timezone
import django.core.validators as validators
from django.utils.translation import gettext_lazy as _
from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_('email address'), unique=True)
    username = models.CharField(max_length=10, default="default", null=True, blank=True)
    first_name = models.CharField(max_length=32, default="Joe")
    last_name = models.CharField(max_length=32, default="Blogs")
    company = models.CharField(max_length=50, default="Orefox")
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)
    credits = models.DecimalField(default=0.0, decimal_places=2, max_digits=65, validators=[validators.MinValueValidator(0.0)])
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.full_name
    
    def natural_key(self):
        return (self.email, self.username)