from django.urls import path, re_path
from lms import views
from django.conf import settings
from django.conf.urls.static import static
from project.models import Permission

app_name = 'lms'

PROJECT_BASE = '<str:slug>/'
OWNER_BASE = PROJECT_BASE + 'o/<str:owner>/'
PARCEL_BASE = PROJECT_BASE + 'p/<uuid:parcel>/'


urlpatterns = [
    path(PROJECT_BASE, views.lms_project, name='lms'),

    path(PROJECT_BASE + 'd', views.ProjectView.as_view(), name='project'),

    # Each view handles the myriad of post requests for each model. These views share very similar logic
    path(PROJECT_BASE + 'p', views.ParcelView.as_view(), name='parcels'),
    path(PROJECT_BASE + 'p/<uuid:parcel>', views.ParcelView.as_view(), name='parcel'),
    path(PROJECT_BASE + 'p/<uuid:parcel>/modify', views.ParcelView.as_view(permission=Permission.ADMIN), name='modify_parcel'),

    path(PROJECT_BASE + 'p/<uuid:parcel>/map', views.MapView.as_view(), name='parcel_map'),

    path(PROJECT_BASE + 'h/<str:model>/<uuid:object>', views.HistoryView.as_view(), name='histories'),
    path(PROJECT_BASE + 'h/<str:model>/<uuid:object>/<uuid:history>', views.HistoryView.as_view(post_permission=Permission.WRITE), name='history'),
    path(PROJECT_BASE + 'h/<str:model>/<uuid:object>/<uuid:history>/r', views.HistoryView.as_view(post_permission=Permission.ADMIN), name='revert_history'),

    # Handling owners is a bit tricky as there's stuff related to only a project or additionally a parcel relationship.
    path(PROJECT_BASE + 'o', views.OwnerView.as_view(), name='owners'),
    path(PROJECT_BASE + 'o/<uuid:owner>', views.OwnerView.as_view(post_permission=Permission.WRITE), name='owner'),
    path(PROJECT_BASE + 'o/<uuid:owner>/modify', views.OwnerView.as_view(post_permission=Permission.WRITE), name='modify_owner'),
    path(PROJECT_BASE + 'o/<uuid:owner>/delete', views.OwnerView.as_view(permission=Permission.WRITE), name='delete_owner'),

    path(PARCEL_BASE + 'r', views.RelationshipView.as_view(), name='relationships'),
    path(PARCEL_BASE + 'r', views.RelationshipView.as_view(), name='relationships_new_owner'),
    path(PARCEL_BASE + 'r/<uuid:relationship>', views.RelationshipView.as_view(post_permission=Permission.WRITE), name='relationship'),
    path(PARCEL_BASE + 'r/<uuid:relationship>/modify', views.RelationshipView.as_view(post_permission=Permission.WRITE), name='modify_relationship'),
    path(PARCEL_BASE + 'r/<uuid:relationship>/delete', views.RelationshipView.as_view(permission=Permission.WRITE), name='delete_relationship'),

    path(PARCEL_BASE + 'r/mail', views.MailView.as_view(), name='relationships_mail'),
    # This stuff is straight forward as it related only to the owner
    path(OWNER_BASE + 'n', views.NoteView.as_view(), name='notes'),
    path(OWNER_BASE + 'n/<uuid:note>', views.NoteView.as_view(post_permission=Permission.WRITE), name='note'),
    path(OWNER_BASE + 'n/<uuid:note>/modify', views.NoteView.as_view(permission=Permission.WRITE), name='modify_note'),
    path(OWNER_BASE + 'n/<uuid:note>/delete', views.NoteView.as_view(permission=Permission.ADMIN), name='delete_note'),

    path(OWNER_BASE + 't', views.TaskView.as_view(), name='tasks'),
    path(OWNER_BASE + 't/<uuid:task>', views.TaskView.as_view(post_permission=Permission.WRITE), name='task'),
    path(OWNER_BASE + 't/<uuid:task>/modify', views.TaskView.as_view(permission=Permission.WRITE), name='modify_task'),
    path(OWNER_BASE + 't/<uuid:task>/delete', views.TaskView.as_view(permission=Permission.ADMIN), name='delete_task'),

    path(OWNER_BASE + 'c', views.CorrespondenceView.as_view(), name='correspondences'),
    path(OWNER_BASE + 'c/<uuid:correspondence>', views.CorrespondenceView.as_view(post_permission=Permission.WRITE), name='correspondence'),
    path(OWNER_BASE + 'c/<uuid:correspondence>/f/<uuid:file>/download', views.CorrespondenceView.as_view(post_permission=Permission.WRITE), name='correspondence_download_file'),
    path(OWNER_BASE + 'c/<uuid:correspondence>/modify', views.CorrespondenceView.as_view(permission=Permission.WRITE), name='modify_correspondence'),
    path(OWNER_BASE + 'c/<uuid:correspondence>/delete', views.CorrespondenceView.as_view(permission=Permission.ADMIN), name='delete_correspondence'),

    path(OWNER_BASE + 'r', views.ReminderView.as_view(), name='reminders'),
    path(OWNER_BASE + 'r/<uuid:reminder>', views.ReminderView.as_view(post_permission=Permission.WRITE), name='reminder'),
    path(OWNER_BASE + 'r/<uuid:reminder>/modify', views.ReminderView.as_view(permission=Permission.WRITE), name='modify_reminder'),
    path(OWNER_BASE + 'r/<uuid:reminder>/delete', views.ReminderView.as_view(permission=Permission.ADMIN), name='delete_reminder'),

    path(OWNER_BASE + 'f', views.FilesView.as_view(), name='files'),
    path(OWNER_BASE + 'f/<uuid:file>', views.FilesView.as_view(post_permission=Permission.WRITE), name='file'),
    path(OWNER_BASE + 'f/<uuid:file>/download', views.FilesView.as_view(post_permission=Permission.WRITE), name='download_file'),
    path(OWNER_BASE + 'f/<uuid:file>/delete', views.FilesView.as_view(permission=Permission.ADMIN), name='delete_file'),
]

if settings.DEBUG:
    urlpatterns += [

    ]
