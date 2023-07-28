import json
import uuid

from django.contrib.auth import get_user_model
from django.contrib.gis.db import models
from django.contrib.gis.geos import MultiPolygon
from django.contrib.gis.db.models.functions import Area
from django.core import serializers
from django.core.exceptions import ValidationError
from django.db.models import UniqueConstraint, CheckConstraint, Q, Sum
from django.urls import reverse
from django.utils.text import slugify

from lms.managers import LandParcelManager, LandParcelProjectManager
from media_file.models import MediaFile
from project.models import Project

User = get_user_model()


class LandParcel(models.Model):
    """A land parcel is described by a lot plan number, the number can be used as lot/plan"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=256)

    # Public information
    lot = models.IntegerField()
    plan = models.CharField(max_length=64)
    tenure = models.CharField(max_length=64)  # tenure or land_use is the category of the land parcel e.g., Freehold, lands lease or state forrest

    geometry = models.MultiPolygonField()

    objects = LandParcelManager()

    @property
    def lot_plan(self):
        return f"{self.lot}/{self.plan}"

    def __str__(self):
        return self.lot_plan

    def area(self):
        # TODO: This is probably not right, not sure how to convert to SQM, has something to do with projection
        self.geometry.transform(3124)
        return self.geometry.area

    # def get_land_size(self):
    #     """Returns the size of land in Square Metres"""
    #     # TODO: Test this to make sure it works, wiki says the CRS type might affect results
    #     return self..annotate(area=Area('mpoly'))


class LandParcelProject(models.Model):
    """This is here in case projects are able to have their own independent instance of a land parcel"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parcel = models.ForeignKey(LandParcel, on_delete=models.CASCADE, related_name='parcel_projects')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='parcel_projects')

    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    user_updated = models.ForeignKey(User, on_delete=models.DO_NOTHING)

    active = models.BooleanField(default=True)  # For if the lot plan is no longer overlapped by the project.

    # Project files within this LandParcel
    files = models.ManyToManyField(MediaFile, related_name='land_parcel_files', blank=True)

    objects = LandParcelProjectManager()

    class Meta:
        unique_together = ('project', 'parcel')
        ordering = ['-date_updated']

    def __str__(self):
        return self.parcel.__str__()

    def file_directory(self):
        """File directory just uses UUID for now."""
        return f"lms/{self.id}"

    @property
    def bulk_mail_target(self):
        """If the user hasn't specified a bulk mail target, just retrieve the most recent entry"""
        return self.owners.order_by('-bulk_mail_target', '-date_created').first()


class LandParcelOwner(models.Model):
    """A person whomst owns a Land Parcel. This model is specific to a LandParcelProject, as Owners are only
    visible/entered by a project owner"""
    # TODO: Do they have to enter this manually themselves?
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
        ('U', 'Undisclosed'),
        ('N', 'N/A'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # FK Project related stuff
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    user_created = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='created_land_parcel_owners')
    user_updated = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='updated_land_parcel_owners')

    parcel = models.ForeignKey(LandParcelProject, on_delete=models.CASCADE, related_name='owners')
    bulk_mail_target = models.BooleanField(default=False)  # Whether the owner is included in the mailing list

    # Personal Details
    first_name = models.CharField(max_length=32)
    last_name = models.CharField(max_length=32)
    preferred_name = models.CharField(max_length=128, null=True, blank=True)
    gender = models.CharField(choices=GENDER_CHOICES, default='N', max_length=1)
    date_birth = models.DateField(null=True, blank=True)

    # Ownership details
    date_ownership_start = models.DateField(null=True, blank=True)
    date_ownership_ceased = models.DateField(null=True, blank=True)

    # Contact Details
    address_street = models.CharField(max_length=512, null=True, blank=True)  # They may live elsewhere to the land parcel
    address_postal = models.CharField(max_length=512, null=True, blank=True)  # They may also accept postage from elsewhere as well
    contact_email = models.EmailField(null=True, blank=True)
    contact_phone = models.CharField(max_length=32, null=True, blank=True)
    contact_mobile = models.CharField(max_length=32, null=True, blank=True)
    contact_fax = models.CharField(max_length=32, null=True, blank=True)

    files = models.ManyToManyField(MediaFile, related_name='land_parcel_owner_files', blank=True)

    class Meta:
        ordering = ['parcel', '-date_updated']
        constraints = [
            # Check to make sure that we only have one owner in the database that is a mail bulk mail target
            # as per Warwick's instructions
            UniqueConstraint(fields=['parcel', 'bulk_mail_target'], condition=Q(bulk_mail_target=True), name='unique_bulk_mail_target_field', violation_error_message="There can only be one bulk mail target per parcel."),
            CheckConstraint(check=Q(bulk_mail_target=True) | ~Q(bulk_mail_target=True), name='valid_bulk_mail_target', violation_error_message="The bulk mail target field must be True or False."),
        ]

    # def clean(self):
    #     if self.bulk_mail_target and self.__class__.objects.filter(parcel=self.parcel, bulk_mail_target=True).exclude(pk=self.pk).exists():
    #         raise ValidationError({'bulk_mail_target': 'There can only be one bulk mail target per parcel'})

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        preferred_name = f' ({self.preferred_name})' if self.preferred_name else ''
        return f"{self.full_name}{preferred_name}"

    def get_context(self):
        return {
            'id': self.id,
            'display': self.__str__(),
            'data': {
                'correspondence': self.correspondence,
                'task': self.tasks,
                'reminder': self.reminders,
                'self.history': self.history,
            }
        }

    def file_directory(self):
        """File directory just uses UUID for now."""
        return self.parcel.file_directory() + f'/{self.id}'


class AbstractInfo(models.Model):
    """Abstract Note Model for attaching notes to some class."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='%(class)s_created_set')
    user_updated = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    owner = models.ForeignKey(LandParcelOwner, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=32)
    content = models.CharField(max_length=512)
    files = models.ManyToManyField(MediaFile, related_name='%(class)s_files', blank=True)

    class Meta:
        abstract = True
        ordering = ['owner', '-date_updated']

    def file_directory(self):
        return f"{self.owner.file_directory()}/{self._meta.get_field('owner').remote_field.related_name}"

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
    owner = models.ForeignKey(LandParcelOwner, related_name='notes', on_delete=models.CASCADE)


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
    owner = models.ForeignKey(LandParcelOwner, related_name='correspondence', on_delete=models.CASCADE)


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
        ('N', 'Not Started'),
        ('I', 'In Progress'),
        ('R', 'Review'),
        ('C', 'Completed'),
    ]
    TASK_PRIORITY = [
        (0, 'None'),
        (1, 'Low'),
        (2, 'Medium'),
        (3, 'High'),
        (4, 'Very High'),
        (5, 'Immediate'),
    ]

    owner = models.ForeignKey(LandParcelOwner, related_name='tasks', on_delete=models.CASCADE)
    status = models.CharField(max_length=1, choices=TASK_STATUS)
    priority = models.IntegerField(choices=TASK_PRIORITY)
    date_due = models.DateField()
    # completed = models.BooleanField(default=False)


class LandParcelOwnerReminder(AbstractInfo):
    """Reminder for a Landowner"""
    owner = models.ForeignKey(LandParcelOwner, related_name='reminders', on_delete=models.CASCADE)
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


class AbstractHistory(models.Model):
    """Abstract model for Model History changes"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='%(class)s_set', unique=False)
    target = models.ForeignKey('self', on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)

    modified_json = models.JSONField()  # Summary of what was changed
    json = models.JSONField()  # Serialized current model

    class Meta:
        abstract = True
        ordering = ['-date_created']

    def revert_to_here(self):
        """Reverts the target model to the changes stored within this instance. Target is not saved by default."""
        # Get the history of updates ahead of this point in time and remove them
        history = self._meta.model.objects.filter(target=self.target, date_created__gt=self.date_created)
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


class LandParcelHistory(AbstractHistory):
    """For tracking changes made to the Land Parcel database model."""
    target = models.ForeignKey(LandParcelProject, related_name='history', on_delete=models.CASCADE)
    model_type = 'parcel'


class LandParcelOwnerHistory(AbstractHistory):
    """For tracking changes made to the Land Parcel Owner database model."""
    target = models.ForeignKey(LandParcelOwner, related_name='history', on_delete=models.CASCADE)
    model_type = 'owner'
