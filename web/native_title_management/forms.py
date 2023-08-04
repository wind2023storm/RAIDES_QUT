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
from native_title_management.models import *


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
