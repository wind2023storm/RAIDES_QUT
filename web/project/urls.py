from django.urls import path

from interactive_map import views as im_views
from . import views
from .utils import post

app_name = 'project'

PROJECT_BASE = 'p/<str:slug>/'

urlpatterns = [
    path('', views.project_index, name='index'),
    path('new_project/', views.new_project, name='new_project'),
    # GET Requests
    # Project Index
    path('get/projects/', views.get_projects, name='get_projects'),
    path('get/tenements/', views.get_tenements, name='get_tenements'),
    path('get/tenements/', views.get_reports, name='get_reports'),

    path('post/create/', post.create_project, name='create_project'),

    # Project Dashboard
    path(PROJECT_BASE, views.project_dashboard, name='dashboard'),
    path(PROJECT_BASE + 'get/tenements/', views.get_project_tenements, name='get_project_tenements'),
    path(PROJECT_BASE + 'get/targets/', views.get_targets, name='get_targets'),
    path(PROJECT_BASE + 'get/tasks/', views.get_tasks, name='get_tasks'),
    path(PROJECT_BASE + 'get/members/', views.get_members, name='get_members'),
    path(PROJECT_BASE + 'get/datasets/', views.get_datasets, name='get_datasets'),
    path(PROJECT_BASE + 'get/models/', views.get_models, name='get_models'),
    path(PROJECT_BASE + 'get/reports/', views.get_reports, name='get_reports'),

    path(PROJECT_BASE + 'get/file/<str:uuid>', views.project_file_download, name='get_file'),

    # Project Map Views
    path(PROJECT_BASE + 'get/project_map/', im_views.get_project_map, name='get_project_map'),
    path(PROJECT_BASE + 'get/tenements_json/', im_views.get_multi_tenements_json, name='get_tenements_json'),
    
    # POST Requests
    path(PROJECT_BASE + 'post/delete/', post.delete_project, name='delete_project'),
    path(PROJECT_BASE + 'post/leave/', post.leave_project, name='leave_project'),

    path(PROJECT_BASE + 'post/tenement/add/', post.add_tenement, name='add_tenement'),

    path(PROJECT_BASE + 'post/target/add/', post.add_target, name='add_target'),
    path(PROJECT_BASE + 'post/target/edit/<str:target_name>', post.edit_target, name='edit_target'),
    path(PROJECT_BASE + 'post/target/delete/', post.delete_target, name='delete_target'),

    path(PROJECT_BASE + 'post/task/add/', post.add_task, name='task_add'),
    path(PROJECT_BASE + 'post/task/delete/', post.delete_task, name='task_delete'),

    path(PROJECT_BASE + 'post/member/invite/', post.invite_member, name='member_invite'),
    path(PROJECT_BASE + 'post/member/delete/', post.delete_member, name='member_delete'),

    path(PROJECT_BASE + 'post/dataset/add/', post.add_dataset, name='dataset_add'),
    path(PROJECT_BASE + 'post/dataset/delete/', post.delete_file, name='dataset_delete'),

    path(PROJECT_BASE + 'post/model/add/', post.add_model, name='model_add'),
    path(PROJECT_BASE + 'post/model/delete/', post.delete_file, name='model_delete'),

    path(PROJECT_BASE + 'post/report/delete/', post.delete_file, name='report_delete'),
]
