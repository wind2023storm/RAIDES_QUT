from django.urls import path, re_path
from native_title_management import views
from django.conf import settings
from django.conf.urls.static import static
from project.models import Permission

app_name = 'nms'

PROJECT_BASE = '<str:slug>/'


urlpatterns = [
    path(PROJECT_BASE, views.nms_project, name='nms'),
]

if settings.DEBUG:
    urlpatterns += [

    ]
