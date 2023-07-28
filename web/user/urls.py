import os

from django.urls import path, re_path, include
from django.conf import settings
from django.contrib.auth import views as auth_views
from . import views

app_name = "user"

urlpatterns = [
    path('', views.home, name='home'),

    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='website:home'), name='logout'),
    path('change_password/', auth_views.PasswordChangeView.as_view(template_name='user/changepassword.html'), name='change_password'),
    path('email/', views.email_view, name='email'),
    path('inactive/', views.inactive_view, name='inactive'),
    path('check_username/', views.check_username, name='check_username'),
    path("password_reset/", views.password_reset_request, name="password_reset"),
    path('reset/<uidb64>/<token>/', views.passwordResetConfirm, name='password_reset_confirm'),
	path('manage/',views.manage_account_view, name='manage',),

]
