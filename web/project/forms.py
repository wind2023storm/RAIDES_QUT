import json
from datetime import datetime
from typing import Union

from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import F, Value
from django.db.models.functions import Concat
from django.forms import DateInput
from django.contrib.auth import get_user_model

from media_file.models import MediaFile
from project.models import Project, ProjectMember, Permission, AustraliaStateChoices
from tms.models import Tenement, Target, TenementTask
from interactive_map.widget import TargetInputWidget

User = get_user_model()


class CreateProjectForm(forms.ModelForm):
    """Create Project Form"""
    class Media:
        css = {'form':"project/css/forms/project_form.css"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            if field.widget.attrs.get('class'):
                field.widget.attrs['class'] += ' form-control'
            else:
                field.widget.attrs['class'] = 'form-control'

    def clean_state(self):
        data = super().clean()
        state = data.get('state')

        # TODO: Modify this to accept different states as they are implemented
        if state != AustraliaStateChoices.QLD:
            self.add_error('state', 'Currently only QLD is supported')

        return state

    class Meta:
        model = Project
        fields = ('name', 'state', 'locality', 'objective',)
        widgets = {
            "name": forms.TextInput(attrs={'placeholder': 'My New Project', 'required' : True}),
            "locality": forms.TextInput(attrs={'placeholder': 'Where is the project located?', 'required' : 'true'}),
            "objective": forms.Textarea(attrs={'placeholder': 'What do you hope to achieve?', 'rows' : 4, 'required' : 'true'}),
        }



class CreateTargetForm(forms.ModelForm):
    """Form for Creating a Target within a given tenement
    Should probably add something to do with location (e.g., lat/lon) though it's possible
    that we can just create targets from the interactive map

    Parameters
    ----------
        instance : Project, Tenement
            Determines what fields are shown and their initial values.
    """
    
    tenements = forms.CharField(widget=forms.HiddenInput())
    created_user = forms.ModelChoiceField(queryset=User.objects.all(), widget=forms.HiddenInput())
    location_input = forms.CharField(label='Location :',
        max_length=100,
        required=True,
        
        widget=forms.TextInput(attrs={
            'id': 'id_location_input',
            'placeholder' :'Click on Map to save Location','autocomplete':False,
            
          }))
    def __init__(self, user, instance=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        all_tenements=[]
        self.fields['location'].label = False
        # If project was supplied as an argument, update the tenement choices to those only within the project
        if isinstance(instance, Project):
            self.fields.pop('project')  # ].initial = instance.id
            all_tenements = instance.tenements.all()
            
        elif isinstance(instance, Tenement):
            all_tenements = instance

        context = [{
                'type': tenement.permit_type,
                'number': tenement.permit_number,
                'display': tenement.permit_id,
                'status': tenement.permit_status,
                'slug': tenement.get_absolute_url(),
        } for tenement in all_tenements]
    
        self.fields['tenements'].initial = json.dumps(context, default=str)
        self.fields['created_user'].initial = user
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['required'] = True  
          
            

    class Meta:
        model = Target
        fields = ('project', 'tenements', 'name', 'location_input','location','description','created_user')
        widgets = {
            'name': forms.TextInput(attrs={'id': 'id_target_name'}),
            'location' : TargetInputWidget,
            "description": forms.Textarea(attrs={'id': 'id_target_description', 'placeholder': 'Add Description...', 'rows' : 4}),
      }       
          



class InviteUserForm(forms.Form):
    """Invites a user to a project, we use e-mail field instead of user foreign key """
    user = forms.EmailField(widget=forms.EmailInput(), label='E-mail')
    permission = forms.ChoiceField(choices=Permission.choices)
    message = forms.CharField(required=True, widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        self._project = kwargs.pop('project', None)
        self._inviter = kwargs.pop('inviter', None)

        super().__init__(*args, **kwargs)

        if self._inviter:
            self._inviter_member = self._project.members.get(user=self._inviter)
            self.fields['permission'].choices = Permission.choices_less(self._inviter_member.permission)

        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

    def clean(self):
        data = self.cleaned_data
        email = data.get('user')
        permission = data.get('permission')

        # Add the instance project
        data['project'] = self._project

        # Check if requesting user is actually a member
        try:
            inviter = self._project.members.get(user=self._inviter)

            # Does the inviter have a greater permission than the invitee's permission
            # TODO: Since bit shifting is used to check permissions this might need to be a bit more secure
            if int(permission) > int(inviter.permission):
                self.add_error('permission', 'Permission must be below your current permission level.')

        except ObjectDoesNotExist:
            self.add_error('__all__', 'You are not a member of this project.')

        # Check if target is already a member
        if email in self._project.members.all().values_list('user__email', flat=True):
            self.add_error('user', f'User is already a member of this project.')

        # TODO: When we implement the SMPT server, this needs to be removed as we'll be sending an invitation e-mail instead
        # Check if the user is found in the system
        try:
            data['user'] = User.objects.get(email=email)
        except ObjectDoesNotExist:
            self.add_error('user', f'User not found in system. In future, an invite e-mail will be sent instead.')

        return data

    def save(self):
        data = self.cleaned_data

        project_member = ProjectMember.objects.create(
            project=self._project,
            user=data.get('user'),
            permission=data.get('permission')
        )

        return project_member


class CreateTaskForm(forms.ModelForm):
    authority = forms.ChoiceField()
    attachments = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True,'required':False}))

    def __init__(self, instance: Union[Tenement, Project] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if isinstance(instance, Tenement):
            # If the target instance is a tenement, we don't need to show the tenement field to the client
            # prefill it and save it for later
            self._project = instance.project
            self._tenement = instance
            self._tenement_field = self.fields.pop('tenement')
            self._tenement_field.value = instance

        elif isinstance(instance, Project):
            self._project = instance
            self.fields['tenement'].choices = instance.tenements.annotate(
                permit_id=Concat('permit_type', Value(' '), 'permit_number', output_field=models.CharField())
            ).values_list('id', 'permit_id')

        # Can't use model properties/methods in queries, so we have to annotate the choice through SQL
        # use e-mail as value since the primary key is still an auto-field
        self.fields['authority'].choices = self._project.members.annotate(
            email=F('user__email'),
            full_name=Concat('user__first_name', Value(' '), 'user__last_name')
        ).values_list('email', 'full_name')

        for field_name, field in self.fields.items():
            if field.widget.attrs.get('class'):
                field.widget.attrs['class'] += ' form-control'
                            
            else:
                field.widget.attrs['class'] = 'form-control'

    def clean(self):
        data = self.cleaned_data

        if not data.get('tenement'):
            data['tenement'] = self._tenement

        tenement = data.get('tenement')
        authority = data.get('authority')
        due_date = data.get('due_date')
        attachments = self.files.getlist('attachments')
        directory = tenement.file_directory() + '/task/'

        # Check Tenement
        if tenement not in self._project.tenements.all():
            self.add_error('tenement', 'Invalid Tenement, not in project.')

        # Clean Authority
        try:
            data['authority'] = self._project.members.get(user__email=authority).user
        except ObjectDoesNotExist:
            self.add_error('authority', 'Invalid User, are they a member of the project?')

        # Clean date
        if due_date < datetime.today().date():
            self.add_error('due_date', 'Invalid Date, it cannot be in the past.')

        # Convert attachments to media files
        data['attachments'] = [
            MediaFile(file=file, tag=MediaFile.TASK, file_path=directory) for file in attachments
        ]

        return data

    def save(self, *args, **kwargs) -> TenementTask:
        # Save the cleaned task into an object
        task = super().save(*args, **kwargs)

        # Save all the attached files and add them to project/task m2m fields
        for media_file in self.cleaned_data.get('attachments'):
            media_file.save()
            task.files.add(media_file)
            self._project.files.add(media_file)

        return task

    class Meta:
        model = TenementTask
        fields = ('tenement', 'authority', 'name', 'description', 'due_date')
        widgets = {
            "description": forms.Textarea(attrs={'placeholder': 'Add Description...', 'rows' : 3}),
 
            'due_date': DateInput(attrs={'type': 'date'}),
        }
