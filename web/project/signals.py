import os

from project.models import Project
from django.db import models
from django.dispatch import receiver

from django.db.models.signals import post_save, pre_delete
from spirit.category.admin.forms import CategoryForm

from . import models as ProjectModels
from spirit.category.models import Category
from spirit.topic.models import Topic
from spirit.category.admin.forms import CategoryForm
#from project_management.models import Board


@receiver(models.signals.pre_delete, sender=Project)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes attachments from filesystem
    when corresponding `Project` object is deleted.
    """
    files = instance.files.all()

    for file in files:
        file.delete()


@receiver(models.signals.m2m_changed, sender=Project.files.through)
def auto_delete_file_on_m2m_changed(sender, instance, action, model, **kwargs):
    """If a file is removed from the project m2m relationship. Delete the file from the filesystem."""
    # print('Project files m2m_changed')
    # print('sender', sender)
    # print('instance', instance)
    # print('action', action)
    # print('model', model)
    # print('kwargs', kwargs)

    # If a removal is done, the model is the mediafile
    if action == 'post_remove':
        model.delete()

    # If a relationship is cleared, the supplied instance is the media file itself
    if action == 'post_clear':
        instance.delete()

@receiver(post_save, sender=ProjectModels.Project)
def set_category(sender, instance, created, **kwargs):
    if created:

        data = {
            'title': instance.name,
            'description': 'title',
            'is_global': True,
            'is_private': True,
            'users': [instance.owner],
            'project_id': instance.id
        }
        categoryForm = CategoryForm(data)
        if (categoryForm.is_valid()):
            categoryForm.save()

@receiver(post_save, sender=ProjectModels.ProjectMember)
def add_category_memeber(sender, instance, created, **kwargs):
    if created:
        category = Category.objects.get(project_id=instance.project.pk)

        category.users.add(instance.user.id)

@receiver(pre_delete, sender=Project)
def delete_category(sender, instance, **kwargs):
    category = Category.objects.filter(project_id=instance.pk)
    category.update(is_removed=True)


"""
@receiver(post_save, sender=models.Project)
def set_board(sender, instance, created, **kwargs):
    if created:
        # now save the board table
        Board.objects.create(name=instance.name, owner=instance.owner)
"""

@receiver(post_save, sender=ProjectModels.ProjectMember)
def add_category_memeber(sender, instance, created, **kwargs):
    if created:
        print("OK")
        category = Category.objects.get(project_id=instance.project.pk)

        category.users.add(instance.user.id)
