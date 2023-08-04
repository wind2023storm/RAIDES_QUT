from functools import reduce

from django.contrib.gis.db import models
from django.contrib.gis.db.models import Union
from django.db.models import Prefetch, Q
from django.contrib.gis.geos import MultiPolygon


class NativeTitleManager(models.Manager):

    def filter_project_area(self, project, **extra_query_args):
        """Returns a queryset of all native titles within a projects' area."""

        # TODO: Make sure this query works, still needs testing
        project_geometry = project.tenements.all().aggregate(
            Union('area_polygons')
        ).get('area_polygons__union')

        if project_geometry:
            return self.filter(geometry__intersects=project_geometry)
        else:
            return self.none()
