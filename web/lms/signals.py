
from django.contrib.gis.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import pre_save, post_save
from django.contrib.gis.geos import MultiPolygon
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType

from lms.models import *
from notification.models import Notification
from project.models import Project
from tms.models import Tenement


@receiver(post_save, sender=Project)
def on_project_created_handler(sender, instance, created, **kwargs):
    """When a project is created, create its parcels automatically."""
    if created and False:
        ProjectParcel.objects.bulk_create_for_project(instance)


@receiver(pre_save, sender=Tenement)
def on_tenement_project_change(sender: Tenement, instance: Tenement, **kwargs):
    """Checks if a Tenement has been assigned to a project"""
    try:
        if instance.pk and instance.area_polygons:
            old_tenement = sender.objects.get(pk=instance.pk)
            old_project = old_tenement.project

            # If project has changed
            if instance.project != old_project:
                # If the tenement has a new project
                if instance.project is not None:
                    ProjectParcel.objects.bulk_create_for_project(
                        instance.project,
                        # Include the tenements geometry to make sure it's in the projects space
                        geometry__intersects=instance.area_polygons
                    )
                    """
                    new_parcels = Parcel.objects.filter(geometry__intersects=instance.area_polygons)\
                        .exclude(parcel_projects__project=instance.project)
    
                    new_parcel_projects = []
                    for new_parcel in new_parcels:
    
                        if new_parcel.parcel_projects:
                            # If there is an inactive parcel project, reactivate it
                            new_parcel.parcel_projects.active = True
                            new_parcel.parcel_projects.save()
                        else:
                            # If it doesn't exist yet, prepare it for a bulk creation
                            new_parcel_project = ProjectParcel(project=instance.project, parcel=new_parcel)
                            new_parcel_projects.append(new_parcel_project)
    
                    # Bulk create any new project parcels, faster than doing it in the loop
                    if new_parcel_projects:
                        ProjectParcel.objects.bulk_create(new_parcel_projects)
                """
                else:
                    ProjectParcel.objects.delete_project_parcels_on_tenement(old_tenement)
                
    except Tenement.DoesNotExist:
        pass


@receiver(pre_save, sender=ProjectParcel)
@receiver(pre_save, sender=ParcelOwnerRelationship)
@receiver(pre_save, sender=ParcelOwner)
def on_parcel_project_change_for_history(sender, instance, **kwargs):
    """Initial handler for checking creating a model history object. Old model instance can only be accessed during
    the `pre_save` signal."""
    try:
        old_instance = sender.objects.get(pk=instance.pk)
    except ObjectDoesNotExist:
        instance.__updated_fields = None
    else:
        instance.__updated_fields = []

        # Loop the model fields and collect field names that were changed.
        for field in instance._meta.get_fields():
            current_value = getattr(instance, field.name)
            previous_value = getattr(old_instance, field.name)

            if current_value != previous_value:
                instance.__updated_fields.append(
                    {'name': field.name.replace('_', ' ').title(), 'from': previous_value, 'to': current_value})


@receiver(post_save, sender=ProjectParcel)
@receiver(post_save, sender=ParcelOwnerRelationship)
@receiver(post_save, sender=ParcelOwner)
def on_parcel_project_create_for_history(sender, instance, created, **kwargs):
    """Final handler for creating a model history object. If the object was actually saved safely we can create the
    object. Has to be done in the `post_save` signal as we can't access related fields unless the instance has a PK."""
    # If our model was created or changed, prepare a summary.
    if created:
        modified_json = []  # f"Created by {instance.user_updated}"
    elif instance.__updated_fields:
        # field_array_str = ', '.join(field.replace('_', ' ').title() for field in instance.__updated_fields)
        # summary = f"{field_array_str} updated by {instance.user_updated}"
        modified_json =json.loads(json.dumps(instance.__updated_fields, indent=4, sort_keys=True, default=str))
    else:
        modified_json = None
   
    # If the model has actually been modified
    if created or modified_json is not None:
        # Create our history model and serialize the state of the instance at this point in time.
        content_type = ContentType.objects.get_for_model(sender)
        LMSHistory.objects.create(
            content_object=instance,
            content_type=content_type,
            object_id=instance.id,
            user=instance.user_updated,
            modified_json=modified_json,  # TODO: Figure out how to format this
            json=serializers.serialize('json', [instance]),
        )


@receiver(models.signals.pre_delete, sender=ParcelOwner)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """Destroys 'files' relationship with project. Project signal will handle file deletion."""
    instance.files.all().delete()
