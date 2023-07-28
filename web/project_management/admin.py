from django.contrib import admin
from . import models


# Register your models here.
@admin.register(models.Task)
class ProjectManagementTaskAdmin(admin.ModelAdmin):
    pass
    # list_display = ('restID', 'title', 'description', 'priority', 'date', 'labels', 'assignees', 'column' ,'task_order''')


@admin.register(models.Comment)
class ProjectManagementCommentAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Column)
class ProjectManagementColumnAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Board)
class ProjectManagementBoardAdmin(admin.ModelAdmin):
    pass
