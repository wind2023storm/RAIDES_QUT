from django import forms
from django.db import models

from . import models
from django.contrib.auth import get_user_model

from .models import UploadDataTypeChoices

User = get_user_model()

class DatasetUploadForm(forms.Form):
    """User File Upload form

    User may have two files, where the second is to be merged into the first based on some column key
    """
    # file_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'placeholder': 'Enter a Filename'}))
    project = forms.ModelChoiceField(None)
    data_type = forms.CharField(max_length=4, widget=forms.Select(choices=UploadDataTypeChoices.choices))

    def __init__(self, projects, *args, **kwargs):
        super(DatasetUploadForm, self).__init__(*args, **kwargs)

        self.fields['project'].queryset = projects
        try:
            self.fields['project'].initial = projects[0]
        except IndexError:
            pass

        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'


class DatacleanForm(forms.Form):
    convertUnits = {
        'unit': forms.CharField(),
        'number': forms.IntegerField()
    }

    potato = {
        'fart': forms.IntegerField(),
        'potato': forms.CharField()
    }