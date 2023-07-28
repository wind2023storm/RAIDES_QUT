from functools import wraps
from http import HTTPStatus

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.gis.geos import GEOSGeometry, Polygon, MultiPolygon
from django.db.models import Prefetch, Subquery, OuterRef
from django.http import JsonResponse, HttpResponseNotFound
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views import View

from lms.forms import *
from main.utils.query_analyze import django_query_analyze
from media_file.forms import CreateMultipleMediaFileForm
from notification.models import Notification
from notification.utils.utils import notify_users, notify_project_members
from project.models import Permission
from project.utils.decorators import has_project_permission


def create_debug_objects(request, project):
    """Creates some LandParcelProjects for debug purposes. Mostly for adding geometry to a model."""
    LandParcel.objects.all().delete()

    def M(geom):
        if isinstance(geom, Polygon):
            geom = MultiPolygon([geom])

        return geom

    # LandParcel
    new_parcels = [
        LandParcel(name="a", lot=73, plan="GEORGE WAY", tenure="Beetles", geometry=M(
                GEOSGeometry(
                    '{"type": "Polygon", "coordinates": [ [ [ 152.802046115000053, -27.371197363999954 ], '
                    '[ 152.802128377000031, -27.371642565999935 ], [ 152.80042878800009, -27.372242642999936 ], '
                    '[ 152.800253558000122, -27.372314421999931 ], [ 152.800342026000067, -27.371760157999972 ], '
                    '[ 152.800975660000063, -27.371536491999962 ], [ 152.801704268000094, -27.371277628999962 ], '
                    '[ 152.802046115000053, -27.371197363999954 ] ] ]}'
                )
            )
        ),
        LandParcel(name="b", lot=42, plan="POTATO VILLAGE", tenure="Starch Free", geometry=M(
                GEOSGeometry(
                    '{"type": "Polygon", "coordinates": [ [ [ 152.802013161000104, -27.371019309999951 ], '
                    '[ 152.802046115000053, -27.371197363999954 ], [ 152.801704268000094, -27.371277628999962 ], '
                    '[ 152.800975660000063, -27.371536491999962 ], [ 152.800342026000067, -27.371760157999972 ], '
                    '[ 152.800253558000122, -27.372314421999931 ], [ 152.798966366000059, -27.372841602999983 ], '
                    '[ 152.798769082000035, -27.372881492999966 ], [ 152.79705668500003, -27.373228138999934 ], '
                    '[ 152.79583883500004, -27.373530005999953 ], [ 152.794812026000045, -27.37356280399996 ], '
                    '[ 152.794229249000068, -27.373905388999958 ], [ 152.79326095700003, -27.374304180999957 ], '
                    '[ 152.791985596000018, -27.373340902999928 ], [ 152.791864025000109, -27.373023448999959 ], '
                    '[ 152.792053970000097, -27.371783619999974 ], [ 152.791469852000091, -27.370661964999954 ], '
                    '[ 152.791429865000055, -27.370111031999954 ], [ 152.791554178000069, -27.369184126999983 ], '
                    '[ 152.791907648000119, -27.367133883999941 ], [ 152.793128277000051, -27.36731894199994 ], '
                    '[ 152.793407875000071, -27.367354100999933 ], [ 152.793245802000115, -27.371205000999964 ], '
                    '[ 152.797433297000111, -27.371466500999929 ], [ 152.80046453600005, -27.371658882999952 ], '
                    '[ 152.800956319000079, -27.371485194999934 ], [ 152.802013161000104, -27.371019309999951 ] ] ]}'
                )
            )
        ),
    ]

    LandParcel.objects.bulk_create(new_parcels)

    # We don't do this with bulk create since bulk create bypasses the save method and won't run signals
    for parcel in LandParcel.objects.all():
        LandParcelProject.objects.create(parcel=parcel, project=project, user_updated=request.user)


# @django_query_analyze
# def render_lms_data(request, project):
#     """Renders all the LMS data for a particular project as HTML."""
#     # No longer in use but the prefetch layers could be useful in the future
#     # parcels = LandParcelProject.objects.filter_project_area(project=project)\
#     parcels = LandParcelProject.objects.filter(project=project) \
#         .select_related('parcel', 'user_updated') \
#         .prefetch_related(
#         'history',
#         'history__user',
#         'history__target',
#         'owners',
#         'owners__history',
#         'owners__history__user',
#         'owners__history__target',
#         'owners__correspondence',
#         'owners__correspondence__owner',
#         'owners__correspondence__files',
#         'owners__correspondence__user',
#         'owners__correspondence__user_updated',
#         'owners__tasks',
#         'owners__tasks__owner',
#         'owners__tasks__files',
#         'owners__tasks__user',
#         'owners__tasks__user_updated',
#         'owners__reminders',
#         'owners__reminders__owner',
#         'owners__reminders__user',
#         'owners__reminders__user_updated',
#         'owners__reminders__files',
#         Prefetch('owners',
#                  # Returns either the bulk mail target for the parcel or the first available owner
#                  queryset=LandParcelOwner.objects.filter(
#                      id__in=Subquery(
#                          LandParcelOwner.objects.filter(
#                              parcel_id=OuterRef('parcel_id')
#                          ).order_by('-bulk_mail_target', '-date_created').values('id')[:1]
#                      )
#                  ), to_attr='mail_target')
#     ).annotate(
#         area=Area("parcel__geometry"),
#     ).all()
#
#     context = {
#         'project': project,
#         'parcels': parcels,
#     }
#
#     return render_to_string("lms/demo_interface.html", context, request=request)


@has_project_permission()
def lms_project(request, project, slug):
    """Base view for retrieving stuff related to a project itself. """

    # LandParcel.objects.filter_project_area(project)
    # create_debug_objects(request, project)

    # Fetch the project parcels and related information.
    # Will likely have the mail target stuff as a property on the model itself as it's important for stuff later on.
    # however, keep it here now as chained queries are faster.
    land_parcels = LandParcelProject.objects.filter(project=project).select_related('parcel').prefetch_related(
        'owners',
        # Prefetch(
        #     'owners',
        #      # Returns either the bulk mail target for the parcel or the first available owner
        #      queryset=LandParcelOwner.objects.filter(
        #              id__in=Subquery(
        #                  LandParcelOwner.objects.filter(
        #                      parcel_id=OuterRef('parcel_id')
        #                  ).order_by('-bulk_mail_target', '-date_created').values('id')[:1]
        #              )
        #          ), to_attr='mail_target'
        #      )
    )

    # Render the initial parcel content
    parcel_context = render_to_string("lms/parcel.html", {
        'project': project,
        'items': land_parcels,
    }, request=request)

    context = {
        'project': project,
        'parcel_content': parcel_context,

        'owner_form': LandParcelOwnerForm(request, project),
        'note_form': LandParcelOwnerNoteForm(request, project),
        'correspondence_form': LandParcelOwnerCorrespondenceForm(request, project),
        'task_form': LandParcelOwnerTaskForm(request, project),
        'reminder_form': LandParcelOwnerReminderForm(request, project),
    }

    return render(request, "lms/lms_base.html", context)


def lms_has_permission(call_before='_call_before'):
    """Permission Handler specific to the LMS. Similar to the original project/tenement one, but tailored more towards
    class based views."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(cls, request, *args, **kwargs):
            action = kwargs.get('action')
            slug = kwargs.get('slug')

            # Get the permission for the incoming action
            permission = cls.action_permissions.get(action, None)

            if permission:
                # Check for the users permission in the project for the action
                project = Project.objects.filter_permission(request, permission, slug=slug).first()

                if project and project.request_member:
                    # Add the project and member to the views class attributes
                    cls.project = project
                    cls.member = project.request_member[0]
                    cls.action = action

                    # Try to call the 'call before' function supplied don't catch AttributeError, so we can make sure
                    # a correct function is being passed for debugging purposes
                    if call_before:
                        try:
                            getattr(cls, call_before)(cls, *args, **kwargs)
                        except ValidationError:
                            return JsonResponse({}, status=HTTPStatus.BAD_REQUEST)

                    # Run the view method e.g., get() or post()
                    return view_func(cls, request, *args, **kwargs)

            # Otherwise everything went wrong and we send unauthorized response
            return JsonResponse({}, status=HTTPStatus.UNAUTHORIZED)

        return wrapped_view

    return decorator


class LmsView(LoginRequiredMixin, View):
    """This is an abstract view used for the majority of LMS views as they all have similar functionality.
    """
    # These just specify what will be used for querying, rendering and validation. Optional unless required by logic.
    template_name = ''
    model = None
    form_class = None

    # For handling specific permissions per action request.
    action_permissions = {
        'get': Permission.READ,
        'new': Permission.WRITE,
        'modify': Permission.WRITE,
        'delete': Permission.ADMIN,
    }

    # These will be set by the decorator
    project = None  # Project this LMS belongs to
    member = None  # User membership model of the project
    action = None  # Action performed

    def _get_query_dict(self):
        """For performing internal queries of the model. The ID field is used for requests targeting a singular object,,
        though will be omitted for querying for a list"""
        return {}

    def _get_instance(self):
        """Returns an individual instance of `cls.model` using `get_query_dict()`. Will throw ObjectDoesNotExist
        exception should the query fail."""
        print(self._get_query_dict())
        return self.model.objects.get(**self._get_query_dict())

    def _get_list(self):
        """Returns a queryset of all `cls.model` under the parent object defined in `get_query_dict()`"""
        query_dict = self._get_query_dict()
        del query_dict['id']
        print(self.model._meta.verbose_name, self.model, query_dict)
        return self.model.objects.filter(**query_dict)

    def _render_queryset(self, queryset):
        """Renders the template specific to displaying this model. Takes in a queryset of what to show."""
        return {
            'html': render_to_string(self.template_name, {'project': self.project, 'member': self.member, 'items': queryset}, request=self.request),
        }

    def _call_before(self, *args, **kwargs):
        """Base method for performing any logic before the view method is called."""
        pass

    @lms_has_permission()
    def get(self, request, *args, **kwargs):
        return JsonResponse(self._render_queryset(self._get_list()), status=HTTPStatus.OK)

    @lms_has_permission()
    def post(self, request, action, *args, **kwargs):
        form_errors = None
        instance = None

        if action in {'modify', 'delete'}:
            try:
                instance = self._get_instance()
            except ObjectDoesNotExist:
                return JsonResponse({}, status=HTTPStatus.NOT_FOUND)

        if action == 'delete':
            instance.delete()
            response = {'id': instance.id}
            instance = None
        else:
            # Don't need an if statement here since valid actions are handled by the decorator,
            # modify and new are implied
            form = self.form_class(request, self.project, request.POST, instance=instance)

            if form.is_valid():
                instance = form.save()
            else:
                form_errors = form.errors

            if not form_errors and request.FILES:
                file_form = CreateMultipleMediaFileForm(
                    instance=instance,  # Change this to model with 'files' field
                    files=request.FILES,
                    tag=self.form_class.FILE_TYPE,
                    allowed_extensions=self.form_class.ALLOWED_EXTENSIONS
                )

                # New media files are stored here, we can add them to another models field
                if file_form.is_valid():
                    media_files = file_form.save()

                    # Add the files to the LandParcelProject, the location of which is dependant on the
                    # model class we have
                    if media_files:
                        file_container_model = None
                        if issubclass(self.model, AbstractInfo):
                            file_container_model = instance.owner.parcel
                        elif self.model is LandParcelOwner:
                            file_container_model = instance.parcel
                        elif self.model is LandParcelProject:
                            file_container_model = instance

                        if file_container_model:
                            for file in media_files:
                                file_container_model.files.add(file)
                else:
                    form_errors = file_form.errors

            # Return any form errors if any had occurred
            if form_errors:
                return JsonResponse(form_errors, status=HTTPStatus.BAD_REQUEST)

            response = self._render_queryset([instance])

        # Handle Project Notification
        verb = {
            'new': 'created',
            'modify': 'modified',
            'delete': 'deleted',
            'revert': 'reverted',
        }.get(action, 'acted upon')

        notify_project_members(
            project=self.project,
            user_from=self.request.user,
            summary=f"{self.model._meta.verbose_name.title()} <b>{instance.__str__().title()}</b> was {verb} by <b>{self.request.user}</b>.",
            target=instance,
            url=reverse('lms:project', kwargs={'slug': self.project.slug})
        )

        return JsonResponse(response, status=HTTPStatus.OK)


class ParcelView(LmsView):
    template_name = 'lms/parcel.html'
    model = LandParcelProject
    form_class = None

    action_permissions = {
        'get': Permission.READ
    }

    def _get_query_dict(self):
        return {
            'id': self.request.GET.get('parcel', None) or self.request.POST.get('parcel', None),
            'project': self.project
        }


class OwnerView(LmsView):
    template_name = 'lms/owner.html'
    model = LandParcelOwner
    form_class = LandParcelOwnerForm

    def _get_query_dict(self):
        return {
            'id': self.request.GET.get('owner', None) or self.request.POST.get('owner', None),
            'parcel': self.request.GET.get('parcel', None) or self.request.POST.get('parcel', None),
            'parcel__project': self.project
        }


class NoteView(LmsView):
    template_name = 'lms/owner_notes.html'
    model = LandParcelOwnerNote
    form_class = LandParcelOwnerNoteForm

    def _get_query_dict(self):
        return {
            'id': self.request.POST.get('note', None) or self.request.GET.get('note', None),
            'owner': self.request.POST.get('owner', None) or self.request.GET.get('owner', None),
            'owner__parcel__project': self.project
        }


class CorrespondenceView(LmsView):
    template_name = 'lms/owner_correspondence.html'
    model = LandParcelOwnerCorrespondence
    form_class = LandParcelOwnerCorrespondenceForm
    
    def _get_query_dict(self):
        return {
            'id': self.request.POST.get('correspondence', None) or self.request.GET.get('correspondence', None),
            'owner': self.request.POST.get('owner', None) or self.request.GET.get('owner', None),
            'owner__parcel__project': self.project
        }
    
    
class ReminderView(LmsView):
    template_name = 'lms/owner_reminders.html'
    model = LandParcelOwnerReminder
    form_class = LandParcelOwnerReminderForm
    
    def _get_query_dict(self):
        return {
            'id': self.request.POST.get('reminder', None) or self.request.GET.get('reminder', None),
            'owner': self.request.POST.get('owner', None) or self.request.GET.get('owner', None),
            'owner__parcel__project': self.project
        }

    
class TaskView(LmsView):
    template_name = 'lms/owner_tasks.html'
    model = LandParcelOwnerTask
    form_class = LandParcelOwnerTaskForm
    
    def _get_query_dict(self):
        return {
            'id': self.request.POST.get('task', None) or self.request.GET.get('task', None),
            'owner': self.request.POST.get('owner', None) or self.request.GET.get('owner', None),
            'owner__parcel__project': self.project
        }


class HistoryView(LmsView):
    template_name = 'lms/parcel_history.html'
    model = None
    form_class = None

    action_permissions = {
        'get': Permission.READ,
        'revert': Permission.ADMIN,
    }

    def _get_owner_query_dict(self):
        return {
            'id': self.request.GET.get('history') or self.request.POST.get('history'),
            'target_id': self.request.GET.get('owner') or self.request.POST.get('owner'),
            'target__parcel__project_id': self.project.id
        }

    def _get_parcel_query_dict(self):
        return {
            'id': self.request.GET.get('history') or self.request.POST.get('history'),
            'target_id': self.request.GET.get('parcel') or self.request.POST.get('parcel'),
            'target__project_id': self.project.id
        }

    def _call_before(self, *args, **kwargs):
        """Changes the model and _get_query_dict functions depending on the model passed through the original view
        argument"""
        # Could have easily split the view in two for the different models, but since they perform the same thing it
        # just felt easier to handle this before the view is called. We're still able to validate whether the URL
        # argument is correct anyway.
        model = kwargs.get('model')

        if model == 'owner':
            self.model = LandParcelOwnerHistory
            self._get_query_dict = self._get_owner_query_dict
        elif model == 'parcel':
            self.model = LandParcelHistory
            self._get_query_dict = self._get_parcel_query_dict
        else:
            raise ValidationError("Invalid Model")

    @lms_has_permission(call_before='_call_before')
    def post(self, request, action, *args, **kwargs):
        """The only post request action handleable by history is a reversion which requires admin privileges."""
        if action != 'revert':
            return JsonResponse({}, status=HTTPStatus.BAD_REQUEST)

        try:
            instance = self._get_instance()
        except ObjectDoesNotExist:
            return JsonResponse({}, status=HTTPStatus.NOT_FOUND)
        else:
            instance.revert_to_here()

        # Handle Project Notification
        notify_project_members(
            project=self.project,
            user_from=self.request.user,
            summary=f"{self.model._meta.verbose_name.title()} <b>{instance}</b> was rolled back by <b>{self.request.user}</b> to {instance.date_created}.",
            target=instance,
            url=reverse('lms:project', kwargs={'slug': self.project.slug})
        )

        return JsonResponse(self._render_queryset([instance]), status=HTTPStatus.OK)


class FileView(LmsView):
    template_name = 'lms/files.html'  # Not set up in similar fashion to other templates yet
    model = MediaFile

    action_permissions = {
        # 'get': Permission.READ,  # Uncomment when this is created. Check get() for more details
        'download': Permission.READ,
        'delete': Permission.ADMIN,
    }

    def _call_before(self, *args, **kwargs):
        """Get the media file for handling respective requests"""
        try:
            file_id = kwargs.get('file_id')
            self.media_file = self.model.objects.get(id=file_id, land_parcel_files__project=self.project)
        except ObjectDoesNotExist:
            raise ValidationError

    @lms_has_permission()
    def get(self, request, *args, **kwargs):
        if self.action == 'get':
            # Complex logic required as many LMS models have a file directory. This would take some
            # additional layered querying similar to the HistoryView
            raise NotImplementedError()

        elif self.action == 'download':
            return self.media_file.to_file_response()
        else:
            return JsonResponse({}, status=HTTPStatus.BAD_REQUEST)

    @lms_has_permission()
    def post(self, request, *args, **kwargs):
        try:
            self.media_file.delete()
        except Exception:
            return JsonResponse({}, status=HTTPStatus.BAD_REQUEST)
        else:
            # Handle Project Notification
            notify_project_members(
                project=self.project,
                user_from=self.request.user,
                summary=f"The file <b>{self.media_file}</b> was deleted by <b>{self.request.user}</b>.",
                url=reverse('lms:project', kwargs={'slug': self.project.slug})
            )

            return JsonResponse({'id': kwargs.get('file_id')}, status=HTTPStatus.OK)
