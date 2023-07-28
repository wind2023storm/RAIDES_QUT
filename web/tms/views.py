from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import QuerySet
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

from interactive_map import views as im_views
from main.utils.query_analyze import django_query_analyze
from media_file.models import MediaFile
from project.forms import CreateTaskForm
from project.models import Permission, ProjectMember
from project.forms import CreateTaskForm, CreateTargetForm
from project.utils.decorators import has_project_permission
from tms.forms import ClaimTenementForm, CreateWorkProgramForm, WorkProgramReceiptForm
from tms.models.models import WorkProgram
from tms.utils import scraper
from main.utils.fields import ChoicesLabelCase

from interactive_map import views as im_views

User = get_user_model()


def home(request):
    return HttpResponse("App Homepage")


@login_required
def dashboard(request, permit_state, permit_type, permit_number):
    """The tenement dashboard is available to everyone and not just members of its presiding project.
    The contents of the page will be changed depending on the above."""

    tenement = Tenement.objects.filter_permission(
        request,
        Permission.READ,
        permit_state=permit_state.upper(),
        permit_type=permit_type,
        permit_number=permit_number
    ).first()

    # Try to scrape if not found
    if not tenement:
        tenement, was_created = scraper.scrape_tenement(permit_state, permit_type, permit_number)

    # If still not found just 404
    if not tenement:
        return HttpResponse('Tenement Not Found', status=HTTPStatus.NOT_FOUND)

    context = {
        'tenement': tenement,
    }

    try:
        # A scraped tenement will throw an attribute error here so just handle for that instead of if statements
        # and an index error will be thrown if the requesting user isn't a member
        member: ProjectMember = tenement.project.request_member[0]
        context = {**context, **{
            'member': member
        }}

        if member.is_write():
            context = {**context, **{
                'createWorkProgramForm': CreateWorkProgramForm(instance=tenement),
                'createWorkProgramReceipt': WorkProgramReceiptForm(),
                'createTaskForm': CreateTaskForm(instance=tenement),
                'createTargetForm': CreateTargetForm(instance=tenement.project, user=request.user),
            }}
    except (AttributeError, IndexError):
        context = {**context, **{
            'claimTenementForm': ClaimTenementForm(user=request.user, tenement=tenement)
        }}

    return render(request, 'tms/tenement_dashboard.html', context)


@has_project_permission()
def get_file(request, tenement, permit_state, permit_type, permit_number, file_uuid):
    # TODO: This func has been implemented on the project, i dont believe its necessary here need to check
    return JsonResponse({}, status=HTTPStatus.NOT_IMPLEMENTED)


@has_project_permission()
def get_targets(request, tenement, permit_state, permit_type, permit_number):
    targets = tenement.project.targets.all()

    context = {
        'targets': [{
            'name': target.name,
            'description': target.description,
            'location': target.location,
            'actions': None,
        } for target in targets],
        'tenement': permit_type + " " + permit_number,
        'tenement_data': im_views.get_tenements_data(),
    }

    return JsonResponse(context, status=HTTPStatus.OK)


@has_project_permission()
def get_tasks(request, tenement, permit_state, permit_type, permit_number):
    tasks = tenement.tasks.all()

    context = {
        'data': [task.as_table_row() for task in tasks]
    }

    return JsonResponse(context, status=HTTPStatus.OK)


@has_project_permission()
def get_workload(request, tenement, permit_state, permit_type, permit_number):
    programs: QuerySet[WorkProgram] = tenement.work_programs.prefetch_related('receipts', 'receipts__file').annotate(
        units_display=ChoicesLabelCase('discipline', WorkProgram.Discipline.units_choices()),
        quantity_display=ChoicesLabelCase('discipline', WorkProgram.Discipline.quantity_choices())
    ).all()  # Work Program Table
    work_program = [{
        'year': program.year,
        'expenditure': program.estimated_expenditure,
        'discipline': program.get_discipline_display(),
        'activity': program.get_activity_display(),
        'units': program.units,
        'units_display': program.units_display,
        'quantity': program.quantity if program.quantity_display != 'N/A' else '',
        'quantity_display': program.quantity_display,  # if program.quantity_display != 'N/A' else '',
        'actions': None,
        'program_id': program.id,
        'receipts': {
            # 'size': MediaFile.bytes_sum_str(program.receipts),
            'files': [{
                'id': receipt.id,
                'name': receipt.name,
                'description': receipt.description,
                'cost': receipt.cost,
                'date_created': receipt.date_created,
                'quantity': receipt.cost,
                'url': tenement.project.get_file_url(receipt.file.id),
                'filename': receipt.file.filename,
                'size': receipt.file.file_size_str
            } for receipt in program.receipts.all()],
        }
    } for program in programs]

    # TODO: Decide whether or not we need to calculate the yearly totals on the backend or not.
    context = {
        'data': work_program,
    }
    return JsonResponse(context, status=HTTPStatus.OK)


@has_project_permission()
def test_form(request, tenement, permit_state, permit_number, permit_type):
    return render(request, "tms/forms/entry_notice_for_private_land.html", {})


from tms.utils.scraper import *


def as_json(request, permit_state, permit_type, permit_number):
    browser = open_browser(DRIVER_PATH, DRIVER_TYPE)

    try:
        tenement_data = scrape_tenement_data(browser, permit_type, permit_number)
        ea_data = scrape_environmental_data(browser, permit_type, permit_number)
    except Exception as e:
        return JsonResponse({'error': e}, status=HTTPStatus.BAD_REQUEST)

    browser.quit()

    return JsonResponse({'tenement': tenement_data, 'environmental_authority': ea_data}, status=HTTPStatus.OK, safe=False)
