from http import HTTPStatus

from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse

from project.models import Permission, Project, ProjectMember
from tms.models import Tenement


def has_project_permission(permission: Permission = Permission.READ, allow_sudo: bool = False):
    """Decorator checks whether requesting user has supplied permission within the project.
    If failed, user will be redirected to project index.

    Wrapped view requires ``slug`` argument.
    Resulting ``Project`` will be passed back to the view as an object or queryset.

    Examples::

        @has_project_permission(Permission.ADMIN)
        def some_project_view(request, project, slug):
            print('User has at least Admin Permissisons!')

        @has_project_permission()
        def some_tenement_view(request, tenement, permit_type, permit_number):
            print('User has at least Read Permissions!')

    Parameters
    ----------
    permission : Permission
        The permission to query
    """

    def decorator(view_func):
        @login_required
        def _wrapped_view(request, *args, **kwargs):

            # If decorator is called on a project view
            slug = kwargs.get('slug')

            # If the decorator is called on a tenement view
            permit_state = kwargs.get('permit_state')
            permit_type = kwargs.get('permit_type')
            permit_number = kwargs.get('permit_number')

            if slug:
                project: Project = Project.objects.filter_permission(request, permission, slug=slug).first()

                context = {
                    'project': project
                }
            elif permit_state and permit_type and permit_number:
                tenement = Tenement.objects.filter_permission(
                    request,
                    permission,
                    permit_state=permit_state.upper(),
                    permit_type=permit_type,
                    permit_number=permit_number
                ).select_related('project').first()

                project: Project = tenement.project

                context = {
                    'tenement': tenement
                }
            else:
                # This probably won't ever get raised since the function is dependent on proper routing.
                raise ValueError("View arguments should include Project slug or Tenement permit state/type/number.")

            if project and project.request_member:
                return view_func(request, **context, **kwargs)
            elif request.POST:
                # Post requests should result in a JSON response
                return JsonResponse({'errors': 'Bad Request'}, status=HTTPStatus.BAD_REQUEST)
            else:
                # Otherwise redirect to the project index
                return redirect(reverse('project:index'), status=HTTPStatus.NOT_FOUND)

        return _wrapped_view

    return decorator
