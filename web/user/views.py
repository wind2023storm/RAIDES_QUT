
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model, authenticate, login as dj_login
from django.contrib import messages
from . import forms
from http import HTTPStatus
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage
from django.db.models.query_utils import Q
from bs4 import BeautifulSoup
from .forms import  SetPasswordForm, PasswordResetForm
from .decorators import user_not_authenticated
from .tokens import account_activation_token
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from user.models import User




# These aren't needed yet as we're using appboard and redirects
@login_required
def home(request):
    # Not needed since we redirect to the appboard home (see register view above)
    return render(request, "user/account.html", {})


def login(request):
    # We're using the django-auth one for now (check urls.py)
    messages.success(request, 'You have successfully logged in!')

    return render(request, "user/login.html", {})


def register_view(request):
    # The registration view
    if request.method == 'POST':
        register_form = forms.RegistrationForm(request.POST)
        if register_form.is_valid():
            # Save contents from form into user
            user = register_form.save()
         
            # Clean password from form
            password = register_form.cleaned_data.get('password1')
            print("user", user,password)
            # Authenticate and login
            user = authenticate(email=user.email, password=password)
            
            dj_login(request, user)
            messages.success(request, 'You have successfully register!')     
            return redirect('appboard:home')
        else:
            err=""
            for field,errors in register_form.errors.items():
                for error in errors:
                    err +=  error + '<br><br>'
                  
            err = err[:-9]      
              
            messages.error(request, format_html(err ))     
    
           
    else:
        register_form = forms.RegistrationForm()
    return render(request, "user/register.html", {'form': register_form})
def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)
        if user is not None:
            dj_login(request, user)
            messages.success(request, 'You have successfully logged in!')
            return redirect('appboard:home')  # Change "home" to the name of your home page URL pattern
        else:
            messages.error(request, 'Invalid Email or Password.')
    return render(request, 'user/login.html')
def check_username(request):
  if request.method == 'POST':
    username = request.POST['username']
    user_exists = User.objects.filter(username=username).exists()
    return JsonResponse({'exists': user_exists})
def check_email(user_email):
 # if request.method == 'POST':
  #  username = request.POST['email']
    email_exists = User.objects.filter(email=user_email).exists()
    return email_exists

# These were used when allauth was still active, not sure what they're for but some of the templates link to them so whatever
@login_required
def inactive_view(request):
    return render(request, "user/account.html", {})


@login_required
def email_view(request):
    return render(request, "user/account.html", {})

def password_reset_request(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            user_email = form.cleaned_data['email']
            associated_user = get_user_model().objects.filter(Q(email=user_email)).first()
            if associated_user:
                subject = "Password Reset request"
                message = render_to_string("user/template_reset_password.html", {
                    'user': associated_user,
                    'domain': get_current_site(request).domain,
                    'uid': urlsafe_base64_encode(force_bytes(associated_user.pk)),
                    'token': account_activation_token.make_token(associated_user),
                    "protocol": 'https' if request.is_secure() else 'http'
                })
                print("email message",message)
                email = EmailMessage(subject, message, to=[associated_user.email])
                if email.send():
                    messages.success(request,mark_safe("Password Reset Email sent")
                    )
                else:
                    messages.error(request, "Email not sent, try again")
                    return render(request, 'user/password_reset.html')
            else:
           # Email does not exist, handle the error or show a message
                messages.error(request, "No user with this email exist")
       
                return render(request, 'user/password_reset.html')
     
            return redirect('user:login')

       

    form = PasswordResetForm()
    return render(
        request=request, 
        template_name="user/password_reset.html", 
        context={"form": form}
        )

def passwordResetConfirm(request, uidb64, token):
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except:
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        if request.method == 'POST':
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Password Changed Successfully.")
                return redirect('user:login')
            else:
                for error in list(form.errors.values()):
                    errorText = BeautifulSoup(str(error), 'html.parser')
                    messages.error(request, errorText.get_text())
                    print("error",errorText.get_text())
                  
        form = SetPasswordForm(user)
        return render(request, 'user/password_reset_confirm.html', {'form': form})
    else:
        messages.error(request, "Link is expired")

    return redirect('user:login')
@login_required
def manage_account_view(request):
    if request.method == 'POST':
        print(request.POST)
        if request.POST.get('first_name') and request.POST.get('last_name'):
            user_first_name = request.POST['first_name']
            user_last_name = request.POST['last_name']
            request.user.first_name = user_first_name         
            request.user.last_name = user_last_name
            request.user.save()
            messages.success(request, "Name Changed Successfully") 
           
                
        if request.POST.get('email'):
            user_email = request.POST['email']
            if(check_email(user_email)):
                messages.error(request, "Email Already taken ") 
               
            else:    
                request.user.email = user_email
                request.user.save()
                messages.success(request, "Email Changed Successfully") 
        if request.POST.get('company'):
            request.user.company = request.POST['company']
            request.user.save()
            messages.success(request, "Company Changed Successfully") 
        if request.POST.get('old_password') and request.POST.get('new_password1'):
            if(request.POST.get('new_password2') == request.POST.get('new_password1')):
                if request.user.check_password(request.POST['old_password']):
                    request.user.set_password(request.POST['new_password1'])
                    request.user.save()
                    messages.success(request, "Password Changed Successfully") 
                else:
                    messages.error(request, "Old password is wrong")
            else:
                    messages.error(request, "Passwords not match")   
                    


    return render(request,"user/account.html",{})
