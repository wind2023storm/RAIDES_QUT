from http import HTTPStatus
from urllib.parse import parse_qs

from django.contrib.gis.db.models.functions import Area
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models import Prefetch, BooleanField, Value, When, Case, Subquery, OuterRef, Model
from django.forms import ModelForm
from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views import View
from django.views.decorators.http import require_POST

from lms.models import *
from lms.forms import *
from main.utils.query_analyze import django_query_analyze
from media_file.forms import CreateMultipleMediaFileForm
from project.models import Permission
from project.utils.decorators import has_project_permission
from django.contrib.gis.geos import GEOSGeometry, Polygon, MultiPolygon


def create_debug_objects(request, project):
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


@django_query_analyze
def render_lms_data(request, project):
    """Renders all the LMS data for a particular project as HTML."""
    # TODO: Make it prettier in the "demo_interface" or change how it's done altogether.

    # parcels = LandParcelProject.objects.filter_project_area(project=project)\
    parcels = LandParcelProject.objects.filter(project=project) \
        .select_related('parcel', 'user_updated') \
        .prefetch_related(
        'history',
        'history__user',
        'history__target',
        'owners',
        'owners__history',
        'owners__history__user',
        'owners__history__target',
        'owners__correspondence',
        'owners__correspondence__owner',
        'owners__correspondence__files',
        'owners__correspondence__user',
        'owners__correspondence__user_updated',
        'owners__tasks',
        'owners__tasks__owner',
        'owners__tasks__files',
        'owners__tasks__user',
        'owners__tasks__user_updated',
        'owners__reminders',
        'owners__reminders__owner',
        'owners__reminders__user',
        'owners__reminders__user_updated',
        'owners__reminders__files',
        Prefetch('owners',
                 # Returns either the bulk mail target for the parcel or the first available owner
                 queryset=LandParcelOwner.objects.filter(
                     id__in=Subquery(
                         LandParcelOwner.objects.filter(
                             parcel_id=OuterRef('parcel_id')
                         ).order_by('-bulk_mail_target', '-date_created').values('id')[:1]
                     )
                 ), to_attr='mail_target')
    ).annotate(
        area=Area("parcel__geometry"),
    ).all()

    context = {
        'project': project,
        'parcels': parcels,
    }

    return render_to_string("lms/demo_interface.html", context, request=request)


@has_project_permission()
def lms_project(request, project, slug):
    """View specific to a kind of project"""

    # LandParcel.objects.filter_project_area(project)
    # create_debug_objects(request, project)

    land_parcels = LandParcelProject.objects.filter(project=project).select_related('parcel').prefetch_related(
        Prefetch('owners',
                 # Returns either the bulk mail target for the parcel or the first available owner
                 queryset=LandParcelOwner.objects.filter(
                     id__in=Subquery(
                         LandParcelOwner.objects.filter(
                             parcel_id=OuterRef('parcel_id')
                         ).order_by('-bulk_mail_target', '-date_created').values('id')[:1]
                     )
                 ), to_attr='mail_target'
                 )
    )

    parcel_context = render_to_string("lms/parcel.html", {
        'project': project,
        'items': land_parcels,
    }, request=request)

    context = {
        'project': project,
        # 'land_parcel': render_lms_data(request, project),
        'parcel_content': parcel_context,
        'owner_form': LandParcelOwnerForm(request, project),
        'note_form': LandParcelOwnerNoteForm(request, project),
        'correspondence_form': LandParcelOwnerCorrespondenceForm(request, project),
        'task_form': LandParcelOwnerTaskForm(request, project),
        'reminder_form': LandParcelOwnerReminderForm(request, project),
    }

    return render(request, "lms/lms_base.html", context)


@has_project_permission(Permission.ADMIN)
def modify_parcel(request, project, slug):
    """Modifying the LandParcelProject. Takes a POST request where the contents of the dictionary are fields to in the
    model to be updated."""
    action = request.META.get('HTTP_ACTION', None)
    parcel_id = request.POST.get('parcel', None)

    try:
        parcel = LandParcelProject.objects.get(project=project, id=parcel_id)
    except ObjectDoesNotExist:
        return JsonResponse({}, status=HTTPStatus.BAD_REQUEST)
    else:
        # TODO: Update fields provided, there are no other actions for this as admin don't have control over
        #   which parcels exist or dont exist.
        parcel.active = not parcel.active
        parcel.save()

    return JsonResponse({'html': render_lms_data(request, project)}, status=HTTPStatus.OK)


def handle_lms_request(request, action: str, project: Project, model_class, model_form, model_query_dict: dict,
                       template: str, allowed_actions=None, allow_post=True):
    """Handles the NEW/MODIFY/DELETE requests for the LMS models. Handles file uploads as well.

    Parameters
    ----------
        request : WSGIRequest
        action : str
            Kind of action e.g., new, modify, delete
        project : Project
            the project in which the request is related to
        model_class
            LMS model class used e.g., `LandParcelOwnerProject` or `LandParcelOwnerNote`
        model_form
            LMS ModelForm used to create/modify e.g., `LandParcelOwnerForm`
        model_query_dict : dict
            query dictionary used to find a specific model for use in actions
        template : str
            name of the template used to render the model content
        allowed_actions : set[str]
            actions not allowed for actions for this method
        allow_post : bool
            Whether post request is allowed for this specific instance

    Returns
    -------
        response : JsonResponse
            Contains either errors or rendered HTML
    """
    print(action, request.GET or request.POST)

    if allowed_actions is None:
        allowed_actions = {'get', 'new', 'modify', 'delete'}

    if action not in allowed_actions:
        return JsonResponse('Invalid Action', status=HTTPStatus.UNAUTHORIZED)

    # Handle post requests. All expect at least write permissions
    if request.POST and project.request_member[0].is_write():
        instance = None
        form_errors = None

        """Begin action handling"""
        if action == 'new':
            form = model_form(request, project, request.POST)
            if form.is_valid():
                instance = form.save()
            else:
                form_errors = form.errors
        else:
            # Remaining actions require the instance
            try:
                instance = model_class.objects.get(**model_query_dict)
            except ObjectDoesNotExist:
                return JsonResponse({}, status=HTTPStatus.NOT_FOUND)

            if action == 'modify':
                form = model_form(request, project, request.POST, instance=instance)
                if form.is_valid():
                    instance = form.save()
                else:
                    form_errors = form.errors

            elif action == 'delete':
                if project.request_member[0].is_admin():
                    instance.delete()
                    instance = None

        """Begin File upload handling"""
        if instance and request.FILES:
            file_form = CreateMultipleMediaFileForm(
                instance=instance,  # Change this to model with 'files' field
                files=request.FILES,
                tag=model_form.FILE_TYPE,
                allowed_extensions=model_form.ALLOWED_EXTENSIONS
            )

            if file_form.is_valid():
                # New media files are stored here, we can add them to another models field
                # TODO: Figure out if we need to add these to project as well (file size tracking)
                media_files = file_form.save()
            else:
                form_errors = file_form.errors

        # Return any form errors if any had occurred
        if form_errors:
            return JsonResponse(form_errors, status=HTTPStatus.BAD_REQUEST)

        # The post request should respond with either
        items = [instance]

    elif request.GET:
        # For a get request we will just return everything in the category
        # del model_query_dict['id']  # We need the whole category so just remove the id field
        # items = model_class.objects.filter(**model_query_dict)
        pass
    else:
        return JsonResponse({}, status=HTTPStatus.METHOD_NOT_ALLOWED)

    # TODO: MOVE START (mode this block into the elif request.GET section)
    del model_query_dict['id']  # We need the whole category so just remove the id field
    items = model_class.objects.filter(**model_query_dict)
    # TODO: MOVE END

    response = {
        'html': render_to_string(template, {
            'project': project,
            'items': items,
        }, request=request),
    }

    return JsonResponse(response, status=HTTPStatus.OK)


@has_project_permission()
def handle_parcel(request, project, slug, action):
    """Reactions to be had with a particular LandParcelOwner Task"""
    return handle_lms_request(
        request,
        action,
        project,
        LandParcel,
        None,  # No new/modify form yet
        {
            'id': request.POST.get('parcel', None) or request.GET.get('parcel', None),
            'project_id': project.id
        },
        'lms/parcel.html',
        allowed_actions={'get'},
    )


@has_project_permission()
def handle_owner(request, project, slug, action):
    """Reactions to be had with a particular LandParcelOwner Task"""
    return handle_lms_request(
        request,
        action,
        project,
        LandParcelOwner,
        LandParcelOwnerForm,
        {
            'id': request.POST.get('owner', None) or request.GET.get('owner', None),
            'parcel': request.POST.get('parcel', None) or request.GET.get('parcel', None),
            'parcel__project_id': project.id
        },
        'lms/owner.html',
    )


@has_project_permission()
def handle_task(request, project, slug, action):
    """Reactions to be had with a particular LandParcelOwner Task"""
    return handle_lms_request(
        request,
        action,
        project,
        LandParcelOwnerTask,
        LandParcelOwnerTaskForm,
        {
            'id': request.POST.get('task', None) or request.GET.get('task', None),
            'owner': request.POST.get('owner', None) or request.GET.get('owner', None),
            'owner__parcel__project_id': project.id
        },
        'lms/owner_tasks.html'
    )


@has_project_permission()
def handle_correspondence(request, project, slug, action):
    """Reactions to be had with a particular LandParcelOwner Correspondence"""
    return handle_lms_request(
        request,
        action,
        project,
        LandParcelOwnerCorrespondence,
        LandParcelOwnerCorrespondenceForm,
        {
            'id': request.POST.get('correspondence', None) or request.GET.get('correspondence', None),
            'owner': request.POST.get('owner', None) or request.GET.get('owner', None),
            'owner__parcel__project_id': project.id
        },
        'lms/owner_correspondence.html'
    )


@has_project_permission()
def handle_reminder(request, project, slug, action):
    """Reactions to be had with a particular LandParcelOwner Reminder"""
    return handle_lms_request(
        request,
        action,
        project,
        LandParcelOwnerReminder,
        LandParcelOwnerReminderForm,
        {
            'id': request.POST.get('reminder', None) or request.GET.get('reminder', None),
            'owner': request.POST.get('owner', None) or request.GET.get('owner', None),
            'owner__parcel__project_id': project.id
        },
        'lms/owner_reminders.html'
    )


@has_project_permission()
def handle_note(request, project, slug, action):
    """Reactions to be had with a particular LandParcelOwner Note"""
    return handle_lms_request(
        request,
        action,
        project,
        LandParcelOwnerNote,
        LandParcelOwnerNoteForm,
        {
            'id': request.POST.get('note', None) or request.GET.get('note', None),
            'owner': request.POST.get('owner', None) or request.GET.get('owner', None),
            'owner__parcel__project_id': project.id
        },
        'lms/owner_notes.html'
    )


@has_project_permission()
def handle_history(request, project, slug, action):
    """Reverts the history of a parcel or owner, this is determined by the supplied action"""
    print(action, request.POST or request.GET)

    # Prepare our inputs from the request
    parent_id = request.GET.get(action) or request.POST.get(action)
    history_id = request.GET.get('history') or request.POST.get('history')

    # Prepare the model related stuff depending on what history we're after
    if action == 'parcel':
        model_class = LandParcel
        model_history_class = LandParcelHistory
        model_query_dict = {'id': history_id, 'target_id': parent_id, 'target__project_id': project.id}
    elif action == 'owner':
        model_class = LandParcelOwner
        model_history_class = LandParcelOwnerHistory
        model_query_dict = {'id': history_id, 'target_id': parent_id, 'target__parcel__project_id': project.id}
    else:
        return JsonResponse({}, status=HTTPStatus.BAD_REQUEST)

    # Do the revert stuff here if we post
    if request.POST:
        try:
            history = model_history_class.objects.get(**model_query_dict)
            print(history.summary)
            history.revert_to_here()
        except Exception as e:
            return JsonResponse({}, status=HTTPStatus.BAD_REQUEST)

    # We're not interested in the ID since we need the whole category
    del model_query_dict['id']

    rendered_response = {
        'html': render_to_string('lms/parcel_history.html', {
            'history_type': action,
            'project': project,
            'items': model_history_class.objects.filter(**model_query_dict),
        }, request=request)
    }

    return JsonResponse(rendered_response, status=HTTPStatus.OK)


@has_project_permission()
def handle_file(request, project, slug):
    rendered_response = {}
    return JsonResponse(rendered_response, status=HTTPStatus.NOT_IMPLEMENTED)