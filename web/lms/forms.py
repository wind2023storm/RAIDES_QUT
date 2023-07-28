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


def form_has_changed_or_files_added(cls):
    """This function handles validation for the models with a files M2M relationship.

    When `form.has_changed()` is called, if the model has files already, so this function handles the following scenarios
    correctly:

    The form has no fields changed, and no files added: returns error
    The form has no fields changed, but files added: form is validated
    """
    fields_changed = bool([name for name, bf in cls._bound_items() if name != 'files' and bf._has_changed()])
    files_added = bool(cls._request.FILES)

    return files_added or fields_changed


class LandParcelOwnerForm(forms.ModelForm):
    """Form for the creation and modification of a LandParcelOwner"""
    FILE_TYPE = MediaFile.DOCUMENT
    ALLOWED_EXTENSIONS = MediaFile.Extensions.DOCUMENT + MediaFile.Extensions.PDF + MediaFile.Extensions.EXCEL + MediaFile.Extensions.DATA + MediaFile.Extensions.IMAGE

    def __init__(self, request, project, *args, **kwargs):
        self._request = request
        self._project = project

        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()

        # If we're modifying the model, check if fields have actually been changed before proceeding.
        if self.instance.pk:
            if not form_has_changed_or_files_added(self):
                raise forms.ValidationError("You must change a field if you wish to update this item.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        if instance.date_created is None:
            instance.user_created = self._request.user

        instance.user_updated = self._request.user

        if commit:
            instance.save()

        return instance

    class Meta:
        model = LandParcelOwner
        exclude = ('user_created', 'user_updated', 'files',)
        widgets = {
            'parcel': forms.TextInput(attrs={'hidden': True}),
            'date_birth': DateInput(attrs={'type': 'date', 'required': False}),
            'date_ownership_start': DateInput(attrs={'type': 'date', 'required': False}),
            'date_ownership_ceased': DateInput(attrs={'type': 'date', 'required': False}),
        }


class CreateInfoForm(forms.ModelForm):
    """Form for the creation and modification of any models that inherit from AbstractInfo. e.g., LandParcelOwnerNote
    and LandParcelOwnerCorrespondence"""
    FILE_TYPE = MediaFile.DOCUMENT
    ALLOWED_EXTENSIONS = MediaFile.Extensions.DOCUMENT + MediaFile.Extensions.PDF + MediaFile.Extensions.EXCEL + MediaFile.Extensions.DATA + MediaFile.Extensions.IMAGE

    def __init__(self, request, project, *args, **kwargs):
        self._request = request
        self._project = project

        super().__init__(*args, **kwargs)

        self.fields['owner'].choices = LandParcelOwner.objects.filter(parcel__project=project)

    def clean(self):
        cleaned_data = super().clean()

        # If we're modifying the model, check if fields have actually been changed before proceeding.
        if self.instance.pk:
            if not form_has_changed_or_files_added(self):
                raise forms.ValidationError("You must change a field if you wish to update this item.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        if instance.date_created is None:
            instance.user = self._request.user
        instance.user_updated = self._request.user

        if commit:
            instance.save()

        return instance

    class Meta:
        model = LandParcelOwnerCorrespondence
        exclude = ('user_updated', 'user',)
        widgets = {
            'owner': forms.TextInput(attrs={'hidden': True}),
            'files': forms.ClearableFileInput(attrs={'multiple': True, 'required': False}),
            'content': forms.Textarea()
        }


class LandParcelOwnerNoteForm(CreateInfoForm):

    def __init__(self, request, project, *args, **kwargs):
        super().__init__(request, project, *args, **kwargs)

    class Meta(CreateInfoForm.Meta):
        model = LandParcelOwnerNote


class LandParcelOwnerCorrespondenceForm(CreateInfoForm):

    def __init__(self, request, project, *args, **kwargs):
        super().__init__(request, project, *args, **kwargs)

    class Meta(CreateInfoForm.Meta):
        model = LandParcelOwnerCorrespondence


class LandParcelOwnerTaskForm(CreateInfoForm):

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
