import uuid
from itertools import chain

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core import serializers
from django.core.serializers import serialize
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import CheckConstraint, Q
from django.forms import model_to_dict

from project.models import Project

User = get_user_model()


class Notification(models.Model):
    """A generic notification model."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Notification information, who did it and what did they do?
    user_from = models.ForeignKey(User, on_delete=models.CASCADE)
    summary = models.CharField(max_length=256)
    url = models.CharField(max_length=100, null=True, blank=True)  # If we need to route to a specific location

    # The target is basically the object in which the notification is for. For example, if a user modifies a project
    # the project would be the target.
    target_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    target_id = models.CharField(max_length=36, null=True, blank=True)
    target = GenericForeignKey('target_type', 'target_id')

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def create_status_for_users(self, **user_query_dict):
        """Creates a NotificationStatus for every user in the user_query_dict"""
        queryset = User.objects.filter(**user_query_dict).exclude(user=self.user_from).all()

        for user in queryset:
            self.status.create(user=user)


class NotificationStatus(models.Model):
    """Relational model for storing user specific information regarding the Notification. e.g., Has the user read
    the notification.
    """
    # TODO: Add this again when the frontend can sort by the timestamp field
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='status')
    is_read = models.BooleanField(default=False)

    class Meta:
        unique_together = ['user', 'notification']
        ordering = ['-notification__timestamp']
