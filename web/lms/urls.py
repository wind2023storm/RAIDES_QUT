from django.urls import path, re_path
from lms import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'lms'

PROJECT_BASE = '<str:slug>/'
PARCEL_BASE = PROJECT_BASE + '/p/<str:parcel_id>'


urlpatterns = [
    path(PROJECT_BASE, views.lms_project, name='project'),

    # Each view handles the myriad of post requests for each model. These views share very similar logic
    path(PROJECT_BASE + 'parcel/<str:action>', views.ParcelView.as_view(), name='handle_parcel'),
    path(PROJECT_BASE + 'owner/<str:action>', views.OwnerView.as_view(), name='handle_owner'),
    path(PROJECT_BASE + 'note/<str:action>', views.NoteView.as_view(), name='handle_note'),
    path(PROJECT_BASE + 'task/<str:action>', views.TaskView.as_view(), name='handle_task'),
    path(PROJECT_BASE + 'correspondence/<str:action>', views.CorrespondenceView.as_view(), name='handle_correspondence'),
    path(PROJECT_BASE + 'reminder/<str:action>', views.ReminderView.as_view(), name='handle_reminder'),

    # Only these two views have larger variation
    path(PROJECT_BASE + 'history/<str:model>/<str:action>', views.HistoryView.as_view(), name='handle_history'),
    path(PROJECT_BASE + 'file/<str:action>/<uuid:file_id>', views.FileView.as_view(), name='handle_file'),
]

if settings.DEBUG:
    urlpatterns += [

    ]
