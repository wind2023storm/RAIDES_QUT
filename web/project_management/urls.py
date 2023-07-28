from django.urls import path
from . import views

app_name="project_management"

urlpatterns = [
    # Create New Project and listing
    path('', views.kanban, name='kanban'), 
    path('board/<str:boardID>', views.get_board, name="get_board"),
    path('task/<str:restID>', views.get_task, name="get_task"),
    path('board', views.create_board, name="board"),
    path('update/board', views.update_board, name="update_board"),
    path('delete/board', views.delete_board, name="delete_board"),
    path('column', views.create_column, name="column"),
    path('column_deletion', views.delete_column, name="delete_column"),
    path('task', views.create_task, name="task"),
    path('update/task', views.update_task, name="update_task"),
    path('delete/task', views.delete_task, name="delete_task"),
    path('search/member', views.search_member, name="search_member"),
]
