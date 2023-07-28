import os
from typing import Union, List

from django import forms
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models

from media_file.models import MediaFile, MediaFileRelationship
from django.contrib.auth import get_user_model

User = get_user_model()


def validate_file_extension(file, allowed_extensions) -> Union[None, str]:
    """Validates a file against allowed file extensions. Returns an error string or None"""
    path_split = os.path.splitext(file.name)

    try:
        # The extension is the second item in the path, which also includes the period at position 0
        # have to remove the period for proper comparisons
        extension = path_split[1][1:]
    except IndexError:
        # File probably didn't have an extension, which is fine if any file extensions were allowed
        extension = ''

    if extension not in allowed_extensions:
        allowed_str = ", ".join(allowed_extensions)
        return f'File extension {extension if extension else "None"} is not allowed. Allowed extensions are: {allowed_str}'

    return None


class MediaFileField(forms.FileField):
    """Simple file field for handling and validating a MediaFile input."""
    # widget = forms.ClearableFileInput(attrs={'multiple': False})

    def __init__(self, tag, *args, **kwargs):
        """A Simple file field for handling and validating a MediaFile. Multiple files require individual validation.

        Parameters
        ----------
        tag : MediaFile tag
        """
        self.tag = tag
        self.allowed_extensions = kwargs.pop('allowed_extensions', None)
        self.file_path = kwargs.pop('file_path', None)

        super().__init__(*args, **kwargs)

        if self.allowed_extensions:
            self.validators = [FileExtensionValidator(allowed_extensions=self.allowed_extensions)]
            # For the extensions to show up in the file selector they have to be prefixed with a full stop
            self.widget.attrs['accept'] = ','.join(['.' + ext for ext in self.allowed_extensions])

    def clean(self, *args, **kwargs):
        file = super().clean(*args, **kwargs)

        if self.allowed_extensions:
            # We need to do additional extension validation as the normal file field
            # validates from the request header. We want to validate the file directly.
            extension_error = validate_file_extension(file, self.allowed_extensions)

            if extension_error:
                raise ValidationError(extension_error)

        return MediaFile(file=file, tag=self.tag, file_path=self.file_path if self.file_path else None)


class CreateMultipleMediaFileForm(forms.Form):
    """This is a basic file upload form with one file field that can handle multiple file uploads"""

    files = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True, 'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        """A Form Capable of uploading multiple MediaFiles at a time. Only requires arguments when validating

        Parameters
        ----------
        instance : object, optional
            An object with a 'files' many-to-many field that where the target is a MediaFile
        tag : MediaFile.TAG_CHOICES, optional
            See MediaFile.TAG_CHOICES for available types
        allowed_extensions : str[]
            List of allowable file extensions, e.g., ['.xlsx', '.csv']
        """
        self._instance = kwargs.pop('instance', None)
        self.tag = kwargs.pop('tag', None)
        self.allowed_extensions = kwargs.pop('allowed_extensions', None)

        super().__init__(*args, **kwargs)

        # Check if the user has specified allowed extensions, these can be forged in the header, but we will perform
        # safe validation on the backend.
        if self.allowed_extensions:
            self.fields['files'].validators = [FileExtensionValidator(allowed_extensions=self.allowed_extensions)]
            # For the extensions to show up in the file selector they have to be prefixed with a full stop
            self.fields['files'].widget.attrs['accept'] = ','.join(['.' + ext for ext in self.allowed_extensions])

    def clean(self):
        # Handle some basic errors, these won't be presented to the client and are for backend debugging purposes only
        if not self.tag >= 0:
            raise TypeError("Requires 'tag' argument in constructor.")

        if not self._instance:
            raise TypeError("Requires 'instance' argument in constructor.")

        if not callable(getattr(self._instance.__class__, 'file_directory')):
            raise AttributeError("Instance must override the 'file_directory()' method.")

        if not hasattr(self._instance.__class__, 'files'):
            raise AttributeError("Instance must have a 'files' many-to-many field.")

        # Begin handling form data
        data = self.cleaned_data
        files = self.files.getlist('files')

        if not len(files):
            self.add_error('files', "Must have at least One file.")

        # Create a blank list for storing new media-files
        data['media_files'] = []
        file_path = self._instance.file_directory()

        for file in files:
            extension_error = validate_file_extension(file, self.allowed_extensions)

            if extension_error:
                self.add_error('file', extension_error)

            # Create and append the media file to the cleaned data
            data['media_files'].append(MediaFile(file=file, tag=self.tag, file_path=file_path))

        return data

    def save(self, *args, **kwargs) -> Union[MediaFile, List[MediaFile]]:

        output = []

        # Save cleaned files and add them to instanced many-to-many field
        for file in self.cleaned_data.get('media_files', []):
            media_file = file.save()
            self._instance.files.add(media_file)
            output += [media_file]

        # return the files
        return output
