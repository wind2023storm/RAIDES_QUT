from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.shortcuts import reverse
from django.utils.formats import localize
from django.views.decorators.http import require_POST

from media_file.forms import CreateMultipleMediaFileForm
from media_file.models import MediaFile
from notification.utils.utils import notify_users, notify_project_members
from project.forms import CreateProjectForm, CreateTargetForm, CreateTaskForm, InviteUserForm
from project.models import Permission, ProjectMember
from project.utils.decorators import has_project_permission
from tms.forms import AddTenementForm
from tms.models import Target, TenementTask
from django.contrib import messages
from interactive_map import views as im_views
import numpy as np

User = get_user_model()

@require_POST
@login_required
def create_project(request):
    form = CreateProjectForm(request.POST or None)
    if form.is_valid():
        project = form.save(commit=False)
        project.owner = request.user
        project.save()

        ProjectMember.objects.create(project=project, user=request.user, permission=Permission.OWNER)
        messages.success(request, 'Project Created Successfully')
    else:
        err=""
        for field,errors in form.errors.items():
            for error in errors:
                 err += error
        return JsonResponse(form.errors, status=HTTPStatus.BAD_REQUEST)
    
    return JsonResponse({'url': project.get_absolute_url()}, status=HTTPStatus.OK)


@require_POST
@has_project_permission(Permission.OWNER)
def delete_project(request, project, slug):
    # Remove the project from all the tenements and save
    for tenement in project.tenements.all():
        tenement.project = None
        tenement.save()
    project.delete()

    # Notify members of the project
    notify_project_members(
        project=project,
        user_from=request.user,
        summary=f"The Project <b>{project.name}</b> was deleted by <b>{request.user}</b>.",
        url=reverse('project:index')
    )

    # Re-direct to the project index
    project_index = reverse('project:index')
    messages.success(request, 'Project Deleted Successfully')
    return JsonResponse({'url': project_index}, status=HTTPStatus.OK)


@require_POST
@has_project_permission(Permission.ADMIN)
def add_tenement(request, project, slug):
    """Post request formed from the Project Index where a user pressed the green "plus" button in the
    "MyTenements" table header."""
    data = request.POST.copy()
    data['project'] = project.slug

    form = AddTenementForm(user=request.user, data=data)

    if form.is_valid():
        tenement = form.save()
        messages.success(request, 'Tenement Added Successfully')

        # Notify members of the project
        notify_project_members(
            project=project,
            user_from=request.user,
            summary=f"The Tenement <b>{tenement}</b> claimed into <b>{project}</b> by <b>{request.user}</b>.",
            url=reverse('project:dashboard', kwargs={'slug': project.slug})
        )

    else:
        err = ""
        for field, errors in form.errors.items():
            for error in errors:
                err += error
        return JsonResponse(form.errors, status=HTTPStatus.BAD_REQUEST)

    return JsonResponse({}, status=HTTPStatus.OK)


@require_POST
@has_project_permission(Permission.ADMIN)
def invite_member(request, project, slug):
    # TODO: This func needs to be changed when the SMTP server is implemented
    form = InviteUserForm(data=request.POST or None, inviter=request.user, project=project)

    if form.is_valid():
        new_member = form.save()

        context = {
            'data': {
                'name': new_member.user.full_name,
                'email': new_member.user.email,
                # TODO: get_permission_display() is supposed to show the string representation but isnt for some reason
                'permission': new_member.get_permission_display(),
                'join_date': localize(new_member.join_date),
                # The inviter is assumed admin due to required permissions so all 3 options are available
                'actions': ['message', 'remove', 'modify'],
            }
        }
        # return JsonResponse(context, status=HTTPStatus.OK)
        messages.success(request, 'Member Invited Successfully')

        # Notify members of the project
        notify_project_members(
            project=project,
            user_from=request.user,
            summary=f"<b>{new_member}</b> was invited to <b>{project}</b> by <b>{request.user}</b>.",
            url=reverse('project:dashboard', kwargs={'slug': project.slug})
        )
       
    else:
        err = ""
        for field, errors in form.errors.items():
            for error in errors:
                err += error
        return JsonResponse(form.errors, status=HTTPStatus.BAD_REQUEST)
    return JsonResponse(context, status=HTTPStatus.OK)


@require_POST
@has_project_permission(Permission.ADMIN)
def delete_member(request, project, slug):
    """Removes a member from the project, they must have a permission lesser than the requesting users permission"""
    target_email = request.POST.get('email')
    request_member = request.user.memberships.get(project=project)

    try:
        target_member = project.members.get(user__email=target_email)

        if request_member.permission > target_member.permission:
            target_member.delete()
            messages.success(request, 'Member Removed Successfully')

            # Notify members of the project
            notify_project_members(
                project=project,
                user_from=request.user,
                summary=f"<b>{target_member}</b> was removed from <b>{project}</b> by <b>{request.user}</b>.",
                url=reverse('project:dashboard', kwargs={'slug': project.slug})
            )

    except ObjectDoesNotExist:
        return JsonResponse({}, status=HTTPStatus.BAD_REQUEST)

    return JsonResponse({}, status=HTTPStatus.OK)


@require_POST
@has_project_permission()
def leave_project(request, project, slug):
    """Post request for leaving a project"""
    try:
        member = request.user.memberships.get(project=project)

        if member.permission == Permission.OWNER:
            return JsonResponse({'project': [{
                'message': 'Owner cannot leave Project',
                'code': 'Not Acceptable'
            }]}, status=HTTPStatus.NOT_ACCEPTABLE)
        else:
            member.delete()
            messages.success(request, 'Leave Project Successfully')

            # Notify members of the project
            notify_project_members(
                project=project,
                user_from=request.user,
                summary=f"<b>{request.user}</b> has left <b>{project}</b>.",
                url=reverse('project:dashboard', kwargs={'slug': project.slug})
            )

    except ObjectDoesNotExist:
        return JsonResponse({'project': [{
            'message': 'Project Not Found',
            'code': 'Not Found'
        }]}, status=HTTPStatus.NOT_FOUND)

    return JsonResponse({}, status=HTTPStatus.OK)


@require_POST
@has_project_permission(Permission.WRITE)
def add_target(request, project, slug):
    post_data = request.POST.copy()
    post_data['project'] = project.id
    #post_data['created_user'] = request.user

    #target_form = CreateTargetForm(data=post_data or None)
    target_form = CreateTargetForm(user=request.user, data=post_data or None)
    if target_form.is_valid():
        target = target_form.save()
        tenements = project.tenements.all()

        project_tenements = [{
                'type': tenement.permit_type,
                'number': tenement.permit_number,
                'slug': tenement.get_absolute_url(),
        } for tenement in tenements]

        context = {
            'data': {
                # TODO: Figure out how the permit column should be populated
                'permit': {'slug': None, 'type': None, 'number': None},
                'name': target.name,
                'description': target.description,
                'location': target.location,
                'actions': None,
            },
        'tenement_data': im_views.get_tenements_data(),
        'project_tenements': project_tenements,
        }
        messages.success(request, 'Target Created Successfully')
        # return JsonResponse(context, status=HTTPStatus.OK)

        # Notify members of the project
        notify_project_members(
            project=project,
            user_from=request.user,
            summary=f"<b>{request.user}</b> created a new target in <b>{project}</b>.",
            url=reverse('project:dashboard', kwargs={'slug': project.slug})
        )
    else:
        err = ""
        for field, errors in target_form.errors.items():
            for error in errors:
               err += error
        return JsonResponse(target_form.errors, status=HTTPStatus.BAD_REQUEST)
    return JsonResponse(context, status=HTTPStatus.OK)

@require_POST
@has_project_permission(Permission.WRITE)
def edit_target(request, project, slug, target_name):

    target = Target.objects.get(project=project, name=target_name)
    post_data = request.POST.copy()
    
    target.name = post_data.get('name')
    target.location = post_data.get('location')
    target.description = post_data.get('description')
    
    target.save()
    print('target save')
    messages.success(request, 'Target Updated Successfully')
    tenements = project.tenements.all()

    project_tenements = [{
            'type': tenement.permit_type,
            'number': tenement.permit_number,
            'slug': tenement.get_absolute_url(),
    } for tenement in tenements]
    # Return the updated target data as JSON
    context = {
            'data': {
                # TODO: Figure out how the permit column should be populated
                'permit': {'slug': None, 'type': None, 'number': None},
                'name': target.name,
                'description': target.description,
                'location': target.location,
                'actions': None,
            },
        'tenement_data': im_views.get_tenements_data(),
        'project_tenements': project_tenements,
        }
    return JsonResponse(context, status=HTTPStatus.OK)



@require_POST
@has_project_permission(Permission.ADMIN)
def delete_target(request, project, slug):
    try:
        target_name = request.POST.get('name')
        target = Target.objects.get(project=project, name=target_name)
        target.delete()
        print("target del")
        messages.success(request, 'Target Deleted Successfully')

        # Notify members of the project
        notify_project_members(
            project=project,
            user_from=request.user,
            summary=f"<b>{request.user}</b> deleted target <b>{target}</b> from <b>{project}</b>.",
            url=reverse('project:dashboard', kwargs={'slug': project.slug})
        )

    except ObjectDoesNotExist as e:
        print(e)
        return JsonResponse({}, status=HTTPStatus.BAD_REQUEST)
        pass

    return JsonResponse({}, status=HTTPStatus.OK)


@require_POST
@has_project_permission(Permission.WRITE)
def add_task(request, project, slug) -> JsonResponse:
    """The 'Add Task' function for creating tasks on the Project Dashboard"""
    
    post_data = request.POST.copy()
    post_data['project'] = project.id

    task_form = CreateTaskForm(data=post_data or None, files=request.FILES or None, instance=project)

    if task_form.is_valid():
        task = task_form.save()

        context = {
            'data': task.as_table_row()
        }
        messages.success(request, 'Task Created Successfully')

        # Notify members of the project
        notify_project_members(
            project=project,
            user_from=request.user,
            summary=f"<b>{request.user}</b> created a new task <b>{task}</b> in <b>{project}</b>.",
            url=reverse('project:dashboard', kwargs={'slug': project.slug})
        )

        # return JsonResponse(context, status=HTTPStatus.OK)
    else:
        err = ""
        for field, errors in task_form.errors.items():
            for error in errors:
                err += error
        return JsonResponse(task_form.errors, status=HTTPStatus.BAD_REQUEST)

    return JsonResponse(context, status=HTTPStatus.OK)


@require_POST
@has_project_permission(Permission.ADMIN)
def delete_task(request, project, slug):
    """Deletes a task from the Database"""

    try:
        task_id = request.POST.get('task', None)
        task = TenementTask.objects.get(tenement__project=project, id=task_id)
        task.delete()
        messages.success(request, 'Task Deleted Successfully')

        # Notify members of the project
        notify_project_members(
            project=project,
            user_from=request.user,
            summary=f"<b>{request.user}</b> deleted the task <b>{task}</b> from <b>{project}</b>.",
            url=reverse('project:dashboard', kwargs={'slug': project.slug})
        )

        return JsonResponse({}, status=HTTPStatus.OK)

    except ObjectDoesNotExist as e:
        pass

    return JsonResponse({}, status=HTTPStatus.BAD_REQUEST)


@require_POST
@has_project_permission(Permission.WRITE)
def add_dataset(request, project, slug):
    """Adds any number of files to the project."""
    dataset_form = CreateMultipleMediaFileForm(
        data=request.POST or None,
        files=request.FILES or None,
        instance=project,
        tag=MediaFile.DATASET,
        allowed_extensions=MediaFile.Extensions.EXCEL + MediaFile.Extensions.DATA
    )

    if dataset_form.is_valid():
        media_files = dataset_form.save()

        context = {'data': [{
            'uuid': str(media.id),
            'file': {
                'url': project.get_file_url(media.id),
                'filename': media.filename,
            },
            'size': media.file_size_str,
            'dateCreated': media.date_created,
            'actions': None,
        } for media in media_files]}

        # Notify members of the project
        notify_project_members(
            project=project,
            user_from=request.user,
            summary=f"<b>{request.user}</b> added <b>{len(media_files)} Datasets</b> to <b>{project}</b>.",
            url=reverse('project:dashboard', kwargs={'slug': project.slug})
        )

        messages.success(request, 'Dataset Added Successfully')

        # return JsonResponse(context, status=HTTPStatus.OK)
    else:
        err = ""
        for field, errors in dataset_form.errors.items():
            for error in errors:
                print("ll", error)
                err += error
        return JsonResponse(dataset_form.errors, status=HTTPStatus.BAD_REQUEST)
    return JsonResponse(context, status=HTTPStatus.OK)


@require_POST
@has_project_permission(Permission.ADMIN)
def delete_file(request, project, slug):
    """Deletes a file that exists within the project. This view is used by delete dataset, model and report"""
    uuid = request.POST.get('uuid')

    try:
        file = project.files.get(id=uuid)
        file.delete()
        messages.success(request, 'File Deleted Successfully')

        # Notify members of the project
        notify_project_members(
            project=project,
            user_from=request.user,
            summary=f"<b>{request.user}</b> deleted <b>{file}</b> from <b>{project}</b>.",
            url=reverse('project:dashboard', kwargs={'slug': project.slug})
        )

    except ObjectDoesNotExist:
        return JsonResponse({}, status=HTTPStatus.NOT_FOUND)

    return JsonResponse({}, status=HTTPStatus.OK)


@require_POST
@has_project_permission(Permission.WRITE)
def add_model(request, project, slug):
    """Adds any number of files to the project."""
    model_form = CreateMultipleMediaFileForm(
        data=request.POST or None,
        files=request.FILES or None,
        instance=project,
        tag=MediaFile.MODEL,
        allowed_extensions=MediaFile.Extensions.MODELS
    )

    if model_form.is_valid():
        media_files = model_form.save()

        context = {'data': [{
            'uuid': str(media.id),
            'file': {
                'url': project.get_file_url(media.id),
                'filename': media.filename,
            },
            'size': media.file_size_str,
            'dateCreated': media.date_created,
            'actions': None,
        } for media in media_files]}

        # Notify members of the project
        notify_project_members(
            project=project,
            user_from=request.user,
            summary=f"<b>{request.user}</b> added <b>{len(media_files)} Models</b> to <b>{project}</b>.",
            url=reverse('project:dashboard', kwargs={'slug': project.slug})
        )

        # return JsonResponse(context, status=HTTPStatus.OK)
        messages.success(request, 'Model Added Successfully')
    else:
        err = ""
        for field, errors in model_form.errors.items():
            for error in errors:
                print("ll", error)
                err += error
        return JsonResponse( model_form.errors, status=HTTPStatus.BAD_REQUEST)

    return JsonResponse(context, status=HTTPStatus.OK)
