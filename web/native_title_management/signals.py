import threading

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.gis.db import models
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import pre_save, post_save
from django.contrib.gis.geos import MultiPolygon
from django.dispatch import receiver
from django.utils import timezone

from lms.models import *
from notification.models import Notification
from project.models import Project
from tms.models import Tenement

#
# @receiver(post_save, sender=Project)
# def on_project_created_handler(sender, instance, created, **kwargs):
#     """When a project is created, create its parcels automatically."""
#     if created and False:
#         ProjectParcel.objects.bulk_create_for_project(instance)

#
# @receiver(pre_save, sender=Tenement)
# def on_tenement_project_change(sender, instance, **kwargs):
#     """Checks if a Tenement has been assigned to a project"""
#     if instance.pk and instance.area_polygons:
#         old_instance = sender.objects.get(pk=instance.pk)
#         old_project = old_instance.project
#
#         # If project has changed
#         if instance.project != old_project:
#             # If the tenement has a new project
#             if instance.project is not None:
#                 ProjectParcel.objects.bulk_create_for_project(
#                     instance.project,
#                     # Include the tenements geometry to make sure it's in the projects space
#                     geometry__intersects=instance.area_polygons
#                 )
#                 """
#                 new_parcels = Parcel.objects.filter(geometry__intersects=instance.area_polygons)\
#                     .exclude(parcel_projects__project=instance.project)
#
#                 new_parcel_projects = []
#                 for new_parcel in new_parcels:
#
#                     if new_parcel.parcel_projects:
#                         # If there is an inactive parcel project, reactivate it
#                         new_parcel.parcel_projects.active = True
#                         new_parcel.parcel_projects.save()
#                     else:
#                         # If it doesn't exist yet, prepare it for a bulk creation
#                         new_parcel_project = ProjectParcel(project=instance.project, parcel=new_parcel)
#                         new_parcel_projects.append(new_parcel_project)
#
#                 # Bulk create any new project parcels, faster than doing it in the loop
#                 if new_parcel_projects:
#                     ProjectParcel.objects.bulk_create(new_parcel_projects)
#
#             else:
#                 # If the tenement no longer has a project deactivate the parcels that no longer intersect
#                 # the project area space. We can't simply deactivate areas that this tenement occupies, in case other
#                 # tenements in the project overlap the same lots.
#                 ProjectParcel.objects.filter(project=old_project).exclude(
#                     parcel__geometry__intersects=models.Union(
#                         MultiPolygon(tenement.area_polygons) for tenement in old_project.tenements.exclude(pk=instance.pk)
#                     )
#                 ).update(active=False)
#             """