from django.contrib.auth.forms import UserCreationForm, UserChangeForm
# from allauth.account import forms as allauth_forms
from django import forms as dj_forms
from django.utils.translation import gettext as _
from django.db import models
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import validate_email

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import  SetPasswordForm, PasswordResetForm
from django.core.exceptions import ValidationError


#class RegistrationForm(UserCreationForm):
#    """
#    User Registration Form, extends django-auth form
#    """
#
#    class Meta:
#        model = User
#        fields = ('email', 'first_name', 'last_name', 'password1', 'password2', )

# class UserChangeForm(UserChangeForm):

#     class Meta:
#         model = User
#         fields = ('email',)


# class LoginForm(allauth_forms.LoginForm):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         for field_name, field in self.fields.items():
#             field.widget.attrs['class'] = 'form-control'



# class SignupForm(allauth_forms.SignupForm):
#     first_name = dj_forms.CharField(
#         label=_("First Name"),
#         widget=dj_forms.TextInput(
#             attrs={"placeholder": _("First Name"), "autocomplete": "first_name"}
#         )
#     )
#     last_name = dj_forms.CharField(
#         label=_("Last Name"),
#         widget=dj_forms.TextInput(
#             attrs={"placeholder": _("Last Name"), "autocomplete": "last_name"}
#         )
#     )







class RegistrationForm(UserCreationForm):
    first_name= forms.CharField( widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name','autocomplete':"off",}))
    last_name= forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}))
    company= forms.CharField( widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company'}))
  
    email = forms.EmailField( widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email','autocomplete':"off",'autofocus':False}))
    password1 = forms.CharField( widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password','autocomplete':"off",'autofocus':False}))
  
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'company','password1', 'password2')

  
  

class LoginForm(AuthenticationForm):
    username = forms.EmailField(widget=forms.EmailInput())

    error_messages = {
        'invalid_login': 'Invalid Email or Password',
        'inactive': 'This account is inactive.',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password'].widget.attrs.update({'autocomplete': 'current-password'})

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            self.user_cache = authenticate(email=username, password=password)
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data

    def get_invalid_login_error(self):
        return ValidationError(
            self.error_messages['invalid_login'],
            code='invalid_login',
            params={'username': self.username_field.verbose_name},
        )

class SetPasswordForm(SetPasswordForm):
    class Meta:
        model = User
        fields = ['new_password1', 'new_password2']

class PasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super(PasswordResetForm, self).__init__(*args, **kwargs)    