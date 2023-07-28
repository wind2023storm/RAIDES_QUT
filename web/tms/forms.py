import copy

from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import FormView
from django.forms.widgets import Select

from forms.forms import CategoryChoiceField
from media_file.forms import MediaFileField
from media_file.models import MediaFile
from project.models import AustraliaStateChoices, Permission, Project
from tms.models import Tenement, PermitTypeChoices, WorkProgram, WorkProgramReceipt
from django.contrib.auth import get_user_model

import numpy as np
from tms.utils import scraper

User = get_user_model()


class AddTenementForm(forms.Form):
    project = forms.ChoiceField()
    permit_state = forms.ChoiceField(choices=AustraliaStateChoices.choices, widget=Select(attrs={'data-category': 'permit_type'}), initial=AustraliaStateChoices.QLD)
    permit_type = CategoryChoiceField(categories=PermitTypeChoices.choices(True))
    permit_number = forms.IntegerField()

    _tenement = None

    def __init__(self, user, *args, **kwargs):

        self._projects = Project.objects.filter(
            members__user=user,
            members__permission__gte=Permission.ADMIN).values_list('slug', 'name')

        self._project: Project = kwargs.pop('project', None)

        super().__init__(*args, **kwargs)

        if not self._project:
            self.fields['project'].choices = self._projects
        else:
            self.fields.pop('project')

        for field_name, field in self.fields.items():
            if field.widget.attrs.get('class'):
                field.widget.attrs['class'] += 'form-control'
            else:
                field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['required'] = True    

    def clean(self):
        data = super().clean()
        project = data.get('project', self._project)
        permit_state = data.get('permit_state')
        permit_type = data.get('permit_type')
        permit_number = data.get('permit_number')

        if project not in self._projects.values_list('slug', flat=True):
            self.add_error('project', 'Invalid Project Choice. Are you an Administrator?')

        if permit_state not in AustraliaStateChoices:
            self.add_error('permit_state', 'Invalid State Choice')

        try:
            PermitTypeChoices.get_display(permit_state, permit_type)
        except IndexError:
            self.add_error('permit_type', 'Permit Type not valid for this State')

        if permit_number < 0:
            self.add_error('permit_number', 'Must be greater than zero')

        # TODO: REMOVE THIS WHEN STATE FILTER HAS BEEN IMPLEMENTED
        if permit_state != AustraliaStateChoices.QLD:
            self.add_error('permit_state', 'Only QLD is currently supported.')

        if permit_state == AustraliaStateChoices.QLD:
            try:
                tenement = Tenement.objects.get(permit_state=permit_state, permit_type=permit_type, permit_number=permit_number)
            except ObjectDoesNotExist:
                tenement, was_created = scraper.scrape_tenement(permit_state, permit_type, permit_number)

            if not tenement:
                self.add_error('__all__', '%s %s Not Found' % (permit_type, permit_number))

            elif tenement.project:
                self.add_error('__all__', '%s %s is already claimed' % (permit_type, permit_number))

            self._tenement = tenement

        print(self.errors)

        return data

    def save(self):
        data = self.cleaned_data
        self._tenement.project = Project.objects.get(slug=data['project'])
        self._tenement.save()

        return self._tenement


class ClaimTenementForm(forms.Form):
    project = forms.ChoiceField()

    def __init__(self, user, tenement, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._tenement = tenement
        self._projects = Project.objects.filter(
            members__user=user,
            members__permission__gte=Permission.ADMIN).values_list('slug', 'name')

        self.fields['project'].widget.attrs['class'] = 'form-control'
        self.fields['project'].choices = self._projects

    def clean_project(self):
        data = super().clean()
        project = data.get('project')

        if self._tenement.project:
            self.add_error('project', 'Tenement is already Claimed')

        if project not in self._projects.values_list('slug', flat=True):
            self.add_error('project', 'Invalid Project Selection')

        return project

    def save(self):
        data = self.cleaned_data
        self._tenement.project = Project.objects.get(slug=data['project'])
        self._tenement.save()

        return self._tenement


class CreateWorkProgramForm(forms.ModelForm, FormView):
    template_name = "tms/forms/work_program_form.html"

    def __init__(self, instance, *args, **kwargs):
        """This CreateWorkProgramForm must be generated using the `{{ createWorkProgramForm }}` tag without the usage of
        `.as_p` etc. This is to ensure that the activity choices will be rendered correctly (as typically form choices
        need to be a list of tuples, but in this case they're a list of lists).

        If you wish to change the visuals of the form, please modify the form stored at `CreateWorkProgramForm.template_name`

        Example Usage ::

            <form>{{ createWorkProgramForm }}</form>
        """
        self._tenement: Tenement = instance

        super(CreateWorkProgramForm, self).__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            if field.widget.attrs.get('class'):
                field.widget.attrs['class'] += 'form-control'
            else:
                field.widget.attrs['class'] = 'form-control'
                

    def clean(self):
        data = self.cleaned_data

        year = data.get('year')
        discipline = data.get('discipline')
        activity = data.get('activity')

        # Just set these to their respective discipline since they align with the labels anyway
        data['units_label'] = discipline
        data['quantity_label'] = discipline

        # Get the valid activities for the selected discipline.
        try:
            valid_ids, valid_activities = tuple(zip(*WorkProgram.Activity.choices_by_discipline(discipline)))
        except IndexError:
            self.add_error('discipline', f"Invalid Discipline.")
            return data

        # Check that the selected activity is available under the selected discipline
        if activity not in valid_ids:
            self.add_error('activity', f"Activity invalid for selected Discipline. Must be one of '{', '.join(valid_activities)}'.")

        # Year can't be greater than the number of terms that the tenement is active for
        if year < 1:
            self.add_error('year', f'Year cannot be less than 1')     
         
        if self._tenement.date_expiry:
            total_terms = self._tenement.term_cumulative
            if year > total_terms:
                self.add_error('year', f'The Tenement has only been approved for {total_terms} terms')
        # Check for the Discipline/Activity/Year uniqueness constraint.
        try:
            WorkProgram.objects.get(tenement=self._tenement, year=year, activity=activity)
            self.add_error('activity', f"A Work Program of this discipline and activity already exists for this term.")
        except ObjectDoesNotExist:
            pass

        return data

    def save(self, *args, **kwargs) -> WorkProgram:
        program = super().save(commit=False)
        program.tenement = self._tenement
        program.save(*args, **kwargs)

        return program

    class Meta:
        model = WorkProgram
        fields = ('year', 'discipline', 'activity', 'units', 'quantity', 'estimated_expenditure')

    def get_context(self):
        """Adds additional context to the form for usage during templating."""
        context = super().get_context()
        context['units_labels'] = WorkProgram.Discipline.units_choices()
        context['quantity_labels'] = WorkProgram.Discipline.quantity_choices()
        context['activity_json'] = WorkProgram.Activity.choices_json()
        return context


class WorkProgramReceiptForm(forms.Form):
    name = forms.CharField()
    description = forms.CharField(widget=forms.Textarea())
    cost = forms.FloatField(min_value=0.0)
    file = MediaFileField(
        tag=MediaFile.RECEIPT,
        allowed_extensions=MediaFile.Extensions.DOCUMENT + MediaFile.Extensions.IMAGE,
        max_length=500
    )

    def __init__(self, work_program=None, *args, **kwargs):

        # Set the media files upload path
        if work_program:
            self.work_program = work_program
            self.declared_fields['file'].file_path = work_program.file_directory()

        # Initialize super class
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            if field.widget.attrs.get('class'):
                field.widget.attrs['class'] += 'form-control'
            else:
                field.widget.attrs['class'] = 'form-control'

    def clean(self):
        data = super().clean()

        print(data)

        if not self.work_program:
            raise ValueError("Validation requires Work Program supplied to constructor.")

        return data

    def save(self, *args, **kwargs):
        data = self.cleaned_data

        # Handle the media file
        media_file = data.pop('file').save()

        # Save the receipt
        receipt = WorkProgramReceipt(**data, file=media_file, work_program=self.work_program)
        receipt.save(*args, **kwargs)

        # Add the file to the parent project
        self.work_program.tenement.project.files.add(receipt.file)

        return receipt
