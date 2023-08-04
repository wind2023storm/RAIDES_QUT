from django.contrib.gis.db import models
from django.contrib.gis.db.models import Union
from django.db.models import Count, Prefetch
from django.contrib.gis.geos import MultiPolygon

from tms.models.models import Tenement

class LandParcelManager(models.Manager):

    def filter_project_area(self, project, **extra_query_args):
        """Returns a queryset of all land parcels within a projects' area. Or the land parcels that exist within
        the geometry of all tenements of a project."""

        project_geometry = project.tenements.all().aggregate(
            Union('area_polygons')
        ).get('area_polygons__union')

        if project_geometry:
            return self.filter(geometry__intersects=project_geometry)
        else:
            return self.none()


class ParcelProjectManager(models.Manager):

    def lms_filter(self, project):
        """
        Filter project parcels with these query:
            - project
            - active=True

        Annotations Included:
            - owners_count: Numbers of owners in the project parcels
        """
        return self.filter(project=project, active=True).select_related('parcel').annotate(owners_count=Count('owners'))

    def bulk_create_for_project(self, project, **extra_query_args):
        """Creates ProjectParcel' for each Parcel overlapping a project' area if not already exists.
        Ideally this would be called when tenements are added to a project.

        Parameters
        ----------
            project : Project
                Project to create parcels for
            **query_dict
                Dictionary used to query for parcels.
        """
        # Filter for all projects in the area and remove parcels that already have a project through created
        from lms.models import Parcel
        new_parcels = Parcel.objects.filter_project_area(project)

        # Create the new LandParcelProjects (cant use bulk create as it bypasses save method which wont call signals)
        self.filter(project=project, parcel__in=new_parcels, active=False).update(active=True)
        for new_parcel in new_parcels.all():
            if(self.filter(project=project, parcel=new_parcel).exists()):
                continue
            new_parcel_project = self.model(project=project, parcel=new_parcel, user_updated=project.owner)
            new_parcel_project.save()

        # Bulk create any new project parcels required, faster than doing it in the loop
        # if new_parcel_projects:
        #     self.bulk_create(new_parcel_projects)

    def delete_project_parcels_on_tenement(self, removed_tenement: Tenement):
        """
        Update project parcels active to False within that tenement, but not the project parcels that overlap with other tenements

        Parameters:
        ----------
            removed_tenement: Tenement
                Tenement to remove, make sure project is not None
        """
        project = removed_tenement.project
        if project is None:
            raise Exception(f'Project is not found in tenement {removed_tenement}')

        if (project.tenements.count() == 1):
            tenement_polygon = project.tenements.all().aggregate(
                Union('area_polygons')
            ).get('area_polygons__union')

            project_parcels = self.filter(project=project).filter(
                parcel__geometry__intersects=tenement_polygon
            )
        else:
            excluding_tenements_polygon = project.tenements.exclude(id=removed_tenement.id).all().aggregate(
                Union('area_polygons')
            ).get('area_polygons__union')
        
            project_parcels = self.filter(project=project).exclude(
                parcel__geometry__intersects=excluding_tenements_polygon
            )

        if project_parcels.exists():
            print('Deleting project parcels from tenement/ Updating active to False', removed_tenement)
            project_parcels.update(active=False)
    
    def filter_tenement_area(self, tenement: Tenement):
        """Returns a queryset of LandParcelsProjects for a tenement"""
        return self.filter(parcel__geometry__intersects=MultiPolygon(tenement.area_polygons))

    def filter_project_area(self, project):
        """Returns a queryset of LandParcelProjects for a specified project. Uses geometry intersection rather than
        referencing the related field.

        Parameters
        ----------
            project : Project
                Project to query for
            create_missing : bool, optional
                Create any LandParcelProjects that haven't been created yet before returning.

        Returns
        -------
            result : Queryset[ProjectParcel]
                Queryset of all LandParcelProjects that intersect a project."""
        # TODO: Figure out if this is important, the ProjectParcel already has a foreign key
        return self.filter(parcel__geometry__intersects=models.Union(
                MultiPolygon(tenement.area_polygons) for tenement in project.tenements
            )
        )
