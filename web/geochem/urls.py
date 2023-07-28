from django.urls import path
from django.conf import settings
from . import views

app_name = 'geochem'

urlpatterns = [
    path('', views.geochem_home, name='geochem_home'),
    path('dataclean', views.handle_dataclean, name='handle_dataclean'),
    path('get_existing_datasets', views.get_existing_datasets, name='get_existing_datasets'),
    path('handle_dataset_upload', views.handle_dataset_upload, name='handle_dataset_upload'),
    path('handle_dataanalysis', views.handle_dataanalysis, name='handle_dataanalysis'),
    path('download_csv/', views.download_csv, name='download_csv'),
]
