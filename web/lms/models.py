import json
import uuid
from datetime import datetime

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db import models
from django.contrib.gis.geos import MultiPolygon
from django.contrib.gis.db.models.functions import Area
from django.core import serializers
from django.core.exceptions import ValidationError
from django.db.models import UniqueConstraint, CheckConstraint, Q, Sum
from django.urls import reverse
from django.utils.text import slugify

from lms.managers import LandParcelManager, ParcelProjectManager
from media_file.models import MediaFile
from project.models import Project
from tms.models import AustraliaStateChoices

User = get_user_model()


class Parcel(models.Model):
    """A land parcel is described by a lot plan number, the number can be used as lot/plan"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Roads and stuff don't have a lot plan
    lot = models.CharField(max_length=5, null=True, blank=True)
    plan = models.CharField(max_length=10, null=True, blank=True)
    tenure = models.CharField(max_length=40, null=True, blank=True)  # tenure or land_use is the category of the land parcel e.g., Freehold, lands lease or state forrest

    segment_parcel = models.CharField(max_length=40, null=True, blank=True, verbose_name="Segment Parcel")
    shire_name = models.CharField(max_length=40, null=True, blank=True, verbose_name="Local Government")
    feature_name = models.CharField(max_length=60, null=True, blank=True, verbose_name="Name")
    alias_name = models.CharField(max_length=400, null=True, blank=True, verbose_name="Alias Name")

    locality = models.CharField(max_length=30, null=True, blank=True)
    parcel_type = models.CharField(max_length=24, null=True, blank=True)
    cover_type = models.CharField(max_length=10, null=True, blank=True)
    accuracy_code = models.CharField(max_length=40, null=True, blank=True)

    smis_map = models.CharField(max_length=100, null=True, blank=True)

    geometry = models.GeometryField()

    objects = LandParcelManager()

    @property
    def lot_plan(self):
        return f"{self.lot}{self.plan}"

    def __str__(self):
        return self.lot_plan

    def area(self):
        # TODO: This is probably not right, not sure how to convert to SQM, has something to do with projection
        self.geometry.transform(3124)
        return self.geometry.area


class ProjectParcel(models.Model):
    """This is here in case projects are able to have their own independent instance of a land parcel"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parcel = models.ForeignKey(Parcel, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    owners = models.ManyToManyField('lms.ParcelOwner', through='lms.ParcelOwnerRelationship', related_name='parcels', blank=True)

    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    user_updated = models.ForeignKey(User, on_delete=models.DO_NOTHING)

    active = models.BooleanField(default=True)  # For if the lot plan is no longer overlapped by the project.

    # Project files within this Parcel
    files = models.ManyToManyField(MediaFile, related_name='land_parcel_files', blank=True)

    # Owners who persist in this project parcel
    objects = ParcelProjectManager()

    history_relation = GenericRelation('LMSHistory')

    class Meta:
        unique_together = ('project', 'parcel')
        ordering = ['-date_updated']

    def __str__(self):
        return self.parcel.__str__()

    def file_directory(self):
        """File directory just uses UUID for now."""
        return f"lms/{self.id}"

    @property
    def bulk_mail_targets(self):
        """If the user hasn't specified a bulk mail target, just retrieve the most recent entry"""
        return self.owners.filter(mail_target=True)


class ParcelOwner(models.Model):
    """Someone who owns one or many Parcel. The information stored here is specific only to the owner. All
    relational information is stored in the ParcelProjectOwnerRelationship model"""

    GENDER_CHOICES = [
        (0, 'N/A'),
        (1, 'Male'),
        (2, 'Female'),
        (3, 'Other'),
        (4, 'Undisclosed'),
    ]

    TITLE_CHOICES = [
        (0, 'N/A'),
        (1, 'Mr'),
        (2, 'Ms'),
        (3, 'Mrs'),
        (4, 'Miss'),
        (5, 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    # FK Project related stuff
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    user_created = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='created_land_parcel_owners')
    user_updated = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='updated_land_parcel_owners')

    # Personal Details
    title = models.PositiveSmallIntegerField(choices=TITLE_CHOICES, default=0)
    first_name = models.CharField(max_length=32)
    last_name = models.CharField(max_length=32)
    preferred_name = models.CharField(max_length=128, null=True, blank=True)
    gender = models.PositiveSmallIntegerField(choices=GENDER_CHOICES, default=0)
    date_birth = models.DateField(null=True, blank=True)

    # Contact Details
    address_street = models.CharField(max_length=512, null=True, blank=True)  # They may live elsewhere to the land parcel
    address_postal = models.CharField(max_length=512, null=True, blank=True)  # They may also accept postage from elsewhere as well

    contact_email = models.EmailField(null=True, blank=True)
    contact_phone = models.CharField(max_length=32, null=True, blank=True)
    contact_mobile = models.CharField(max_length=32, null=True, blank=True)
    contact_fax = models.CharField(max_length=32, null=True, blank=True)

    # TODO: Does this files field go in the through relationship or not
    files = models.ManyToManyField(MediaFile, related_name='land_parcel_owner_files', blank=True)

    history_relation = GenericRelation('LMSHistory')

    class Meta:
        ordering = ['-date_updated']
        unique_together = ['project', 'title', 'first_name', 'last_name', 'date_birth', 'gender']

    def get_full_name(self):
        return f"{self.get_title_display() + ' ' if self.title > 0 else ''}{self.first_name} {self.last_name}"

    def get_age(self):
        """Returns the age of the person in years"""
        date_start = self.date_birth
        date_end = datetime.today()
        years = date_end.year - date_start.year

        # Adjust the difference if the end date hasn't occurred yet in the current year
        if (date_start.month, date_end.day) < (date_start.month, date_end.day):
            years -= 1

        return years

    def __str__(self):
        preferred_name = f' ({self.preferred_name})' if self.preferred_name else ''
        return f"{self.get_full_name()}{preferred_name}"

    def file_directory(self):
        """File directory just uses UUID for now."""
        return f'lms/{self.project.id}/{self.id}'


class ParcelOwnerRelationship(models.Model):
    """Model that indicates relational information between a Parcel Project and Parcel Owner"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parcel = models.ForeignKey(ProjectParcel, on_delete=models.CASCADE, related_name="owner_relationships")
    owner = models.ForeignKey(ParcelOwner, on_delete=models.CASCADE, related_name="parcel_relationships")

    # Relational Information
    is_mail_target = models.BooleanField(default=False)  # Whether the owner is included in the mailing list

    date_ownership_start = models.DateField(null=True, blank=True)
    date_ownership_ceased = models.DateField(null=True, blank=True)

    # FK Project related stuff
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    user_created = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='created_land_parcel_relationships')
    user_updated = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='updated_land_parcel_relationships')

    history_relation = GenericRelation('LMSHistory')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['parcel', 'owner'], name='unique_parcel_owner', violation_error_message='The Owner already exists within this Parcel.')
        ]

    def __str__(self):
        return self.owner.__str__()


class AbstractInfo(models.Model):
    """Abstract Note Model for attaching notes to some class."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(ParcelOwner, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=32)
    content = models.CharField(max_length=512)

    # History Related
    user_created = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='%(class)s_created_set')
    user_updated = models.ForeignKey(User, on_delete=models.DO_NOTHING)

    class Meta:
        abstract = True
        ordering = ['owner', '-date_updated']

    def __str__(self):
        return self.name


"""
User Story 5: As a user, I want to be able to make notes on landowners, so that I can keep track of important information.
**Acceptance Criteria:**

- The LMS should have a notes section for each landowner.
- The notes section should be easy to use and understand.
- Users should be able to add, view, and edit notes for each landowner.
"""


class LandParcelOwnerNote(AbstractInfo):
    """Notes made on the Land Parcel Owner"""
    owner = models.ForeignKey(ParcelOwner, related_name='notes', on_delete=models.CASCADE)


"""
User Story 6: As a user, I want to be able to upload and store correspondence with landowners, so that I can keep track 
of important documents.
**Acceptance Criteria:**

- The LMS should have a file storage section for each landowner.
- The file storage section should be easy to use and understand.
- Users should be able to upload and view documents for each landowner.
"""


class LandParcelOwnerCorrespondence(AbstractInfo):
    """Correspondence made with the Land Parcel Owner"""
    owner = models.ForeignKey(ParcelOwner, related_name='correspondence', on_delete=models.CASCADE)

    # File deleted with correspondence
    files = models.ManyToManyField(MediaFile, related_name='land_parcel_owner_correspondence_files', blank=True)

    def file_directory(self):
        """File directory just uses UUID for now."""
        return f'{self.owner.file_directory()}/{self.id}'


"""
User Story 9: As a user, I want to be able to assign tasks and reminders for landowners, so that I can keep track of 
important deadlines and events
**Acceptance Criteria:**

- The LMS should have a task management feature that allows users to assign tasks and reminders to specific landowners 
    or land parcels.
- Users should be able to set due dates and priorities for the tasks.
- The tasks should be visible to all users with access to the LMS.
- Users should be able to view and track the status of the tasks and mark them as completed or overdue.
- Users should receive notifications and reminders for upcoming tasks or deadlines.
"""


class LandParcelOwnerTask(AbstractInfo):
    """Task for a Landowner"""
    TASK_STATUS = [
        (0, 'Not Started'),
        (1, 'In Progress'),
        (2, 'Review'),
        (3, 'Completed'),
        (4, 'On hold'),
    ]

    TASK_PRIORITY = [
        (0, 'None'),
        (1, 'Low'),
        (2, 'Medium'),
        (3, 'High'),
        (4, 'Very High'),
        (5, 'Immediate'),
    ]

    owner = models.ForeignKey(ParcelOwner, related_name='tasks', on_delete=models.CASCADE)
    status = models.PositiveSmallIntegerField(choices=TASK_STATUS, default=0)
    priority = models.PositiveSmallIntegerField(choices=TASK_PRIORITY, default=2)
    date_due = models.DateField()

    class Meta:
        ordering = ['-status', '-priority', 'owner', '-date_updated']


class LandParcelOwnerReminder(AbstractInfo):
    """Reminder for a Landowner"""
    owner = models.ForeignKey(ParcelOwner, related_name='reminders', on_delete=models.CASCADE)
    date_due = models.DateField()

"""
User Story 11: As a user, I want to be able to track the history of changes made to landowner and land parcel 
information, so that I can keep a record of important changes and updates.
**Acceptance Criteria:**

- The LMS should have an audit log feature that tracks changes made to landowner and land parcel information, 
    including who made the change and when.
- Users should be able to view the history of changes for each landowner or land parcel.
- The audit log should be secure and tamper-proof.
"""


class LMSHistory(models.Model):
    """Abstract model for Model History changes"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='%(class)s_set', unique=False)
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.CharField(max_length=36, null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    date_created = models.DateTimeField(auto_now_add=True)

    modified_json = models.JSONField()  # Summary of what was changed
    json = models.JSONField()  # Serialized current model

    class Meta:
        ordering = ['-date_created']

    def revert_to_here(self):
        """Reverts the target model to the changes stored within this instance. Target is not saved by default."""
        # Get the history of updates ahead of this point in time and remove them

        # history = self._meta.model.objects.filter(content_object=self.content_object, date_created__gt=self.date_created)
        history = self._meta.model.objects.filter(content_type=self.content_type, object_id=self.object_id, date_created__gt=self.date_created)
        history.delete()

        # Deserialize and collect the fields and values excluding many to many fields into a dict
        obj = next(serializers.deserialize('json', self.json)).object
        updated_values = {
            field.name: getattr(obj, field.name) for field in obj._meta.fields if field not in obj._meta.many_to_many
        }

        # Update the database entry with the values. This will skip the pre_save and post_save signals for the target.
        obj._meta.model.objects.filter(id=obj.id).update(**updated_values)

    def __str__(self):
        return f"{self.id} ({self.date_created})"
