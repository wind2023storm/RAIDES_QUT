from django.core.exceptions import ObjectDoesNotExist


from spirit.topic.forms import TopicForm
from spirit.category.models import Category
from spirit.topic.models import Topic
from tms.models import Tenement, TenementTask, WorkProgramReceipt, Target
from django.db import models
from django.dispatch import receiver


@receiver(models.signals.pre_delete, sender=TenementTask)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """Destroys 'files' relationship with project. Project signal will handle file deletion."""
    files = instance.files.all()

    for file in files:
        file.project_files.clear()


@receiver(models.signals.pre_delete, sender=WorkProgramReceipt)
def auto_delete_receipt_file_on_delete(sender, instance, **kwargs):
    """Destroys 'file' relationship with project. Project signal will handle file deletion."""
    instance.file.project_files.clear()


@receiver(models.signals.pre_save, sender=Tenement)
def auto_add_complaince_tasks(sender, instance: Tenement, **kwargs):
    """Automatically adds complaince tasks to a Tenement if it was either created,
    or claimed by a project. The tasks added are depending on the tenement type.
    """

    # Instance project is the project of the tenement being saved
    instance_project = instance.project

    try:
        # Old project is the project of the instance before it's been saved/updated
        old_project = Tenement.objects.get(id=instance.id).project
    except ObjectDoesNotExist:
        old_project = None

    # Generate complaince documents if the project has changed from None, this occurs during
    # creating a new tenement or claiming it.
    if old_project is None and instance_project:
        # TODO: Attach a media file if we have to
        TenementTask.objects.generate_complaince_documents(instance)

@receiver(models.signals.post_save, sender=Target)
def set_category(sender, instance, created, **kwargs):
    if created:
        category = Category.objects.get(project_id=instance.project.pk)
        print(category.id)
        data = {
            'title': instance.name,
            'category': category,
            'target_id':instance.id

        }
        topicForm = TopicForm(user=instance.created_user, data=data, current="TargetCreationForm")
        print(topicForm.is_valid())
        print(topicForm.errors)
        if (topicForm.is_valid()):
            topicForm.save()

@receiver(models.signals.pre_delete, sender=Target)
def delete_target(sender, instance, **kwargs):
        topic = Topic.objects.filter(target_id=instance.id)
        topic.update(is_removed=True)
