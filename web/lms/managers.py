from django.contrib.gis.db import models
from django.db.models import Prefetch
from django.contrib.gis.geos import MultiPolygon


class LandParcelManager(models.Manager):

    def filter_project_area(self, project, **extra_query_args):
        """Returns a queryset of all land parcels within a projects' area. Or the land parcels that exist within
        the geometry of all tenements of a project."""

        # TODO: Make sure this query works, still needs testing
        tenements = project.tenements.all()
        combined_area = tenements.aggregate(area=models.Union('area_polygons'))['area']

        if combined_area:
            return self.filter(geometry__intersects=combined_area, **extra_query_args)
        else:
            return self.none()


class LandParcelProjectManager(models.Manager):

    def bulk_create_for_project(self, project, **extra_query_args):
        """Creates LandParcelProject' for each LandParcel overlapping a project' area if not already exists.
        Ideally this would be called when tenements are added to a project.

        Parameters
        ----------
            project : Project
                Project to create parcels for
            **query_dict
                Dictionary used to query for parcels.
        """
        # Filter for all projects in the area and remove parcels that already have a project through created
        from lms.models import LandParcel
        new_parcels = LandParcel.objects.filter_project_area(project).exclude(parcel_projects__project=project, **extra_query_args)

        # Create the new LandParcelProjects (cant use bulk create as it bypasses save method which wont call signals)
        for new_parcel in new_parcels.all():
            new_parcel_project = self.model(project=project, parcel=new_parcel, user_updated=project.owner)
            new_parcel_project.save()

        # Bulk create any new project parcels required, faster than doing it in the loop
        # if new_parcel_projects:
        #     self.bulk_create(new_parcel_projects)

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
            result : Queryset[LandParcelProject]
                Queryset of all LandParcelProjects that intersect a project."""
        # TODO: Figure out if this is important, the LandParcelProject already has a foreign key
        return self.filter(parcel__geometry__intersects=models.Union(
                MultiPolygon(tenement.area_polygons) for tenement in project.tenements
            )
        )
