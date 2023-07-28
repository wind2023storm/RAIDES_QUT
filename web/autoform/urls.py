from django.urls import path, re_path
from autoform import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'autoform'

urlpatterns = [
    path('', views.application_for_epm, name='home'),
]

if settings.DEBUG:
    urlpatterns += [

    ]
