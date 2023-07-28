from django.urls import path
from . import views

app_name = 'website'

urlpatterns = [
    path('', views.website_home, name='home'),
    path('message/', views.contact_message, name='contact_message'),
]
