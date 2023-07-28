import os

from django.urls import path, re_path, include
from django.conf import settings
from . import views
from .utils import post
from interactive_map import views as im_views

app_name = 'tms'

# Base URL for a permit, we need to include the permit state for when we need to handle multiple permit types
PERMIT_PATH = '<str:permit_state>/<str:permit_type>/<str:permit_number>/'

urlpatterns = [
    # Get Requests
    path(PERMIT_PATH, views.dashboard, name='dashboard'),
    path(PERMIT_PATH + 'get/file/<uuid:file_uuid>', views.get_file, name='get_file'),
    path(PERMIT_PATH + 'get/targets/', views.get_targets, name='get_targets'),
    path(PERMIT_PATH + 'get/tasks/', views.get_tasks, name='get_tasks'),
    path(PERMIT_PATH + 'get/workload/', views.get_workload, name='get_workload'),

    path(PERMIT_PATH + 'get/test_form/', views.test_form, name='get_test_form'),

    # Project Map Views
    path(PERMIT_PATH + 'get/tenement_map/', im_views.get_tenement_map, name='get_tenement_map'),
    path(PERMIT_PATH + 'get/tenements_json/', im_views.get_tenements_json, name='get_tenements_json'),
    
    # Post Requests
    path(PERMIT_PATH + 'post/claim/', post.claim_tenement, name='claim_tenement'),
    path(PERMIT_PATH + 'post/relinquish/', post.relinquish_tenement, name='relinquish_tenement'),

    path(PERMIT_PATH + 'post/task/add/', post.add_task, name='add_task'),
    path(PERMIT_PATH + 'post/task/delete/', post.delete_task, name='delete_task'),
    path(PERMIT_PATH + 'post/task/archive/', post.archive_task, name='archive_task'),
    path(PERMIT_PATH + 'post/task/modify/', post.modify_task, name='modify_task'),

    path(PERMIT_PATH + 'post/target/add/', post.add_target, name='add_target'),
    path(PERMIT_PATH + 'post/target/delete/', post.delete_target, name='delete_target'),
    path(PERMIT_PATH + 'post/target/modify/', post.modify_target, name='modify_target'),

    path(PERMIT_PATH + 'post/workload/add/', post.add_workload, name='add_workload'),
    path(PERMIT_PATH + 'post/workload/delete/', post.delete_workload, name='delete_workload'),
    path(PERMIT_PATH + 'post/workload/modify/', post.modify_workload, name='modify_workload'),

    path(PERMIT_PATH + 'post/workload/receipt/<str:work_program>/add/', post.add_workload_receipt, name='add_workload_receipt'),

    path(PERMIT_PATH + 'json/', views.as_json, name='as_json'),
]
