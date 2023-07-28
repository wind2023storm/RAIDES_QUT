from django.core.exceptions import ObjectDoesNotExist
from django.core.handlers.wsgi import WSGIRequest
from django.db import models
from django.db.models import Prefetch, Count


class ProjectManager(models.Manager):

    def filter_permission(self, request: WSGIRequest, permission: int, **kwargs):
        """Filters for a project and prefetches the requesting user as a member under the attribute `request_member`
        If `request_member` is an empty list the assumption is that the user does not have correct permissions

        Parameters
        ----------
        request : WSGIRequest
        permission : Permission to check for
        kwargs : Filter arguments for the project model
        """
        return self.filter(**kwargs).prefetch_related(
            Prefetch('members',
                     queryset=request.user.memberships.filter(permission__gte=permission).select_related('user'),
                     to_attr='request_member')
        )

    @staticmethod
    def has_permission(user, permission: int, project):
        if user.is_superuser:
            return True

        try:
            project.members.get(user=user, permission__gte=permission)
            return True
        except ObjectDoesNotExist:
            return False

    def to_datatable(self, request, **kwargs):
        """Prepares a project queryset for use in a frontend datatable. Query parameters are supplied as kwargs, and
        requesting user is assumed to be logged in."""
        projects = self.filter(**kwargs).prefetch_related(
            Prefetch('members', queryset=request.user.memberships.all(), to_attr='request_member')
        ).annotate(
            tenement_count=Count('tenements', distinct=True),
            file_count=Count('files', distinct=True),
        ).all()

        return {
            'data': [{
                'name': project.name,
                'slug': project.get_absolute_url(),
                'state': project.state,
                'permission': project.request_member[0].get_permission_display(),
                'dateCreated': project.created_at,
                'tenementCount': project.tenement_count,
                'fileCount': project.file_count,
                'diskUsage': project.disk_space_usage_str(),
                'credits': project.credits,
                'tags': None,
                'actions': project.request_member[0].permission,  # Probably handle this with a function

            } for project in projects if project.request_member]
        }
