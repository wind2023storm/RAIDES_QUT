import json
from datetime import datetime
from mimetypes import guess_type
from typing import Union

from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import F, Value
from django.db.models.functions import Concat
from django.forms import DateInput
from django.contrib.auth import get_user_model

from media_file.forms import validate_file_extension
from media_file.models import MediaFile
from lms.models import *


def form_has_changed_or_files_added(form):
    """This function handles validation for the models with a files M2M relationship.

    When `form.has_changed()` is called, if the model has files already, so this function handles the following scenarios
    correctly:

    The form has no fields changed, and no files added: returns error
    The form has no fields changed, but files added: form is validated
    """
    def try_get_attr(instance, attr, default=False):
        try:
            return getattr(instance, attr)
        except AttributeError:
            return default

    if form.instance:
        fields_changed = [key for key, value in form.cleaned_data.items() if try_get_attr(form.instance, key, value) != value and key != 'files']
        files_added = form.request.FILES

        print(fields_changed)

        return bool(fields_changed) or bool(files_added)

    return False


class ParcelOwnerForm(forms.ModelForm):
    """Form for the creation and modification of a ParcelOwner"""
    FILE_TYPE = MediaFile.DOCUMENT
    ALLOWED_EXTENSIONS = MediaFile.Extensions.DOCUMENT + MediaFile.Extensions.PDF + MediaFile.Extensions.EXCEL + MediaFile.Extensions.DATA + MediaFile.Extensions.IMAGE

    def __init__(self, request, project, parcel=None, *args, **kwargs):
        self.request = request
        self.project = project
        self.parcel = parcel

        super().__init__(*args, **kwargs)

        del self.fields['project']

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data['project'] = self.project

        # if not form_has_changed_or_files_added(self):
        #     self.add_error(None, "You must change a field if you wish to update this item.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        if instance.date_created is None:
            instance.user_created = self.request.user

        instance.user_updated = self.request.user

        if commit:
            instance.save()

        return instance

    class Meta:
        model = ParcelOwner
        exclude = ('user_created', 'user_updated')
        widgets = {
            'date_birth': DateInput(attrs={'type': 'date', 'required': False}),
            'files': forms.ClearableFileInput(attrs={'multiple': True, 'required': False}),
            'project': forms.TextInput(attrs={'hidden': True}),
        }


class ParcelOwnerRelationshipForm(forms.ModelForm):

    def __init__(self, request, project, parcel=None, owner=None, is_modify=False, *args, **kwargs):
        self.request = request
        self.project = project
        self.parcel = parcel
        self.owner = owner

        super().__init__(*args, **kwargs)

        # As the relationship owner should not be modifiable
        if is_modify:
            del self.fields['owner']
        else:
            self.fields['owner'].choices = [(owner.id, owner.get_full_name()) for owner in
                                            ParcelOwner.objects.filter(project=self.project)]

    def clean(self):
        cleaned_data = super().clean()
        self.owner = cleaned_data['owner'] = cleaned_data.get('owner', self.owner)
        self.parcel = cleaned_data['parcel'] = cleaned_data.get('parcel', self.parcel)

        # Need to remove errors for the owner field if it was removed during the init phase
        if 'owner' not in self.data and 'owner' in cleaned_data:
            del self.errors['owner']

        # Ensure Parcel and Owner belong to same project
        if self.parcel.project != self.owner.project:
            self.add_error('__all__', "Owner and Parcel must belong to the same Project")

        # Owner must not exist in parcel already
        if self.instance:
            unique_parcel_owner = ParcelOwnerRelationship.objects.filter(owner=self.owner, parcel=self.parcel).exclude(pk=self.instance.pk)

            if unique_parcel_owner.exists():
                self.add_error('owner', 'The Owner already exists within this Parcel.')

        # if not form_has_changed_or_files_added(self):
        #     self.add_error(None, "You must change a field if you wish to update this item.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        instance.parcel = self.parcel
        instance.owner = self.owner

        if instance.date_created is None:
            instance.user_created = self.request.user

        instance.user_updated = self.request.user

        if commit:
            instance.save()

        return instance

    class Meta:
        model = ParcelOwnerRelationship
        exclude = ('parcel', 'user_created', 'user_updated')
        widgets = {
            'date_ownership_start': DateInput(attrs={'type': 'date', 'required': False}),
            'date_ownership_ceased': DateInput(attrs={'type': 'date', 'required': False}),
            'parcel': forms.TextInput(attrs={'disabled': True, 'hidden': True}),
        }


class CreateInfoForm(forms.ModelForm):
    """Form for the creation and modification of any models that inherit from AbstractInfo. e.g., LandParcelOwnerNote
    and LandParcelOwnerCorrespondence"""
    FILE_TYPE = MediaFile.DOCUMENT
    ALLOWED_EXTENSIONS = MediaFile.Extensions.DOCUMENT + MediaFile.Extensions.PDF + MediaFile.Extensions.EXCEL + MediaFile.Extensions.DATA + MediaFile.Extensions.IMAGE


    def __init__(self, request, project, owner=None, *args, **kwargs):
        self.request = request
        self.project = project
        self.owner = owner

        super().__init__(*args, **kwargs)

        del self.fields['owner']
        del self.fields['user_created']

    def clean(self):
        cleaned_data = super().clean()

        # If we're modifying the model, check if fields have actually been changed before proceeding.
        cleaned_data['owner'] = self.owner

        if not form_has_changed_or_files_added(self):
            self.add_error(None, "You must change a field if you wish to update this item.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        if instance.date_created is None:
            instance.user_created = self.request.user

        instance.user_updated = self.request.user

        if commit:
            instance.save()

        return instance

    class Meta:
        model = LandParcelOwnerCorrespondence
        exclude = ('user_updated', 'user',)
        widgets = {
            # 'files': ,
            'content': forms.Textarea(attrs={'class': 'align-top'})
        }


class LandOwnerNoteForm(CreateInfoForm):

    def __init__(self, request, project, *args, **kwargs):
        super().__init__(request, project, *args, **kwargs)

    class Meta(CreateInfoForm.Meta):
        model = LandParcelOwnerNote


class LandOwnerCorrespondenceForm(CreateInfoForm):

    files = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True, 'required': False}),
                            required=False)

    def __init__(self, request, project, *args, **kwargs):
        super().__init__(request, project, *args, **kwargs)

    class Meta(CreateInfoForm.Meta):
        model = LandParcelOwnerCorrespondence


class LandOwnerTaskForm(CreateInfoForm):

    def __init__(self, request, project, *args, **kwargs):
        super().__init__(request, project, *args, **kwargs)

    class Meta(CreateInfoForm.Meta):
        model = LandParcelOwnerTask
        widgets = CreateInfoForm.Meta.widgets.copy()
        widgets.update({
            'date_due': DateInput(attrs={'type': 'date'})
        })


class LandParcelOwnerReminderForm(CreateInfoForm):

    def __init__(self, request, project, *args, **kwargs):
        super().__init__(request, project, *args, **kwargs)

    class Meta(CreateInfoForm.Meta):
        model = LandParcelOwnerReminder
        widgets = CreateInfoForm.Meta.widgets.copy()
        widgets.update({
            'date_due': DateInput(attrs={'type': 'date'})
        })
