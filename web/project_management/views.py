from datetime import datetime
import json
import string
import random
from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.core.paginator import EmptyPage, Paginator
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse, response
from django.core import serializers
from django.db.models import F, Q
from datetime import datetime

from . import models
from user.models import User
#from data_processors import models as data_processors_models
from .forms import CreateTaskForm



def try_find_choice(cls, key):
    """Finds a choice from a value, can either be the key or label of a choice

    Parameters
    ----------
        cls : Choice Model
            A TextChoices model
        key : str
            Key to find
    """
    name, label = tuple(zip(*cls.choices))

    if key in name:
        return cls[key].value

    if key in label:
        choices = dict(zip(label, name))
        return cls(choices[key]).value

    return None

@login_required
def kanban(request):
    """
    Creating new project.
    """
    template_name = 'project_management/kanban.html'
    context = {
        'own_boards': models.Board.objects.filter(owner=request.user),
        'boards': models.Board.objects.filter(members=request.user).filter(~Q(owner=request.user)),
    }
    return render(request, template_name, context)

@login_required
def create_board(request):
    """
    Create new board
    """
    if request.method == 'POST':
        data = request.POST
        try:
            board = models.Board.objects.create(name=data.get('name'), owner=request.user)

            members_data = json.loads(data.get("members"))

            board.members.add(*[member["pk"] for member in members_data])

        except:
            return JsonResponse(data={}, status=HTTPStatus.BAD_REQUEST)
        
        template_name = 'project_management/kanban.html'
        context = {

        }

        data = {

        }

        return JsonResponse(data=data, content_type="application/json")
    
@login_required
def delete_board(request):
    """
    Delete a board
    """ 
    if request.method == 'POST':
        data = request.POST

        deleting_board = models.Board.objects.get(id = data.get("id"))
        deleting_board.delete()

        return JsonResponse({}, status=HTTPStatus.OK)
    return JsonResponse({})

@login_required
def update_board(request):
    """
    Update a board
    """
    if request.method == 'POST':
        data = request.POST
        board_id = data.get('id')

        if board_id is None or board_id.strip() == "":
            return JsonResponse({}, status= HTTPStatus.BAD_REQUEST)

        board = models.Board.objects.get(id= board_id)

        updated_name = data.get('name')
        if updated_name != None and updated_name.strip() != "":
            board.name = updated_name

        board.save()


        return JsonResponse({}, status=HTTPStatus.OK)

@login_required
def search_member(request):
    """Search a member"""

    if request.method != "GET": return

    request_data = request.GET
    query = request_data.get('query')

    print("Searching member " + query)
    search_filter = Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(email__icontains=query)

    members_list = list(User.objects.exclude(id = request.user.id).filter(search_filter).all()[:10])
    members_data = serializers.serialize('json', members_list)

    data = {
        "members": members_data
    }

    return JsonResponse(data=data, status=HTTPStatus.OK)

@login_required
def create_column(request):
    """
    Create column in given board
    """
    if request.method == 'POST':
        data = request.POST

        board = models.Board.objects.get(id=data.get('boardID'))

        column = models.Column.objects.create(restID=data.get('id'), title=data.get("title"), board=board)

        data = {

        }

        return JsonResponse(data=data, content_type="application/json")

@login_required
def delete_column(request):
    """
    Delete column in given board
    """
    if request.method == 'POST':
        data = request.POST
        update={}
        update['is_valid']=0
        id = data.get('id')
        # print(id)
        models.Column.objects.filter(id=data.get("id")).update(**update)

        data = {
        }

        return JsonResponse(data=data, content_type="application/json")

@login_required
def create_task(request):
    """
    Create card in given column
    """
    if request.method == 'POST':

        # Split the emails into a list we can use for querying
        assignees = request.POST.get("assignees").split(",")

        # The form data on the website doesn't quite match the fields in the actual model, so
        # we have to build the dict ourselves (another reason why Django Forms are great)
        # two 'id' type fields are passed through, taskID is the restID for the task, while id is the restID
        # for the column (very confusing).
        fields = {
            'restID': request.POST.get('taskID', None),  # The ID for the actual Task
            'title': request.POST.get('title', None),
            'priority': try_find_choice(models.Priority, request.POST.get('priority', None)),
            'description': request.POST.get('description', None),
            'task_order': int(request.POST.get('task_order')),
            'date': request.POST.get("due_date", datetime.today().strftime('%Y-%m-%d')),
            'file': request.FILES.get('file', None),
            'column': models.Column.objects.get(restID=request.POST.get("id", None)),
        }
        if not fields['date']:
            fields['date'] = datetime.today().strftime('%Y-%m-%d')

        # Create the Task object
        task = models.Task.objects.create(**fields)
        task.assignees.set(User.objects.filter(email__in=assignees))
        task.save()

        data = {
        }

        return HttpResponse(json.dumps(data), status=200, content_type='application/json')


def update_task(request):
    """
    Update given task card
    """
    if request.method == 'POST':
        data = request.POST
        update = {}
        task = models.Task.objects.get(restID=data.get("taskID"))
        update["column"] = task.column

        if data.get("id") != None and data.get("id") != task.column.restID:
            update["column"] = models.Column.objects.get(restID=data.get("id"))

        if data.get("title") != None:
            update["title"] = data.get("title")
        if data.get("priority") != None:
            update["priority"] = try_find_choice(models.Priority, data.get("priority"))
        if data.get("description") != None:
            update["description"] = data.get("description")
        if data.get("task_order") != None:
            update["task_order"] = int(data.get("task_order"))

            updated_column = update["column"]
            if updated_column.restID == task.column.restID:
                if task.task_order < update["task_order"]:
                    models.Task.objects.filter(column=updated_column, task_order__gt=task.task_order, task_order__lte=update["task_order"]).update(task_order = F("task_order") - 1)
                else:
                    models.Task.objects.filter(column=updated_column, task_order__gte=update["task_order"], task_order__lt=task.task_order).update(task_order = F("task_order") + 1)
            else:
                models.Task.objects.filter(column=task.column, task_order__gt=task.task_order).update(task_order = F("task_order") - 1)
                models.Task.objects.filter(column=updated_column, task_order__gte=update["task_order"]).update(task_order = F("task_order") + 1)

        if data.get("due_date") != "" and data.get("due_date") != None:
            update["date"] = datetime.strptime(data.get("due_date"), '%Y-%m-%d')

        models.Task.objects.filter(restID=data.get("taskID")).update( **update)
        task = models.Task.objects.get(restID=data.get("taskID"))
        if data.get("assignees") != None:
            assignees = data.get("assignees").split(",")
            try:
                users = User.objects.filter(email__in=assignees)
            except:
                users= []
            task.assignees.set(users)

        task.save()
        
        data = {
        }

        return JsonResponse(data=data, content_type="application/json")

def get_board(request, boardID):
    """
    Get board
    """
    if request.method == "GET":
        board = models.Board.objects.get(id=boardID)
        try:
            columns = models.Column.objects.filter(board=board,is_valid = 1)
            try:
                serialized_columns = serializers.serialize('json', columns)
            except:
                serialized_columns = serializers.serialize('json', [columns])
        except models.Column.DoesNotExist:
            serialized_columns = []
        try:
            column_ids = set(column.id for column in columns)
            tasks = models.Task.objects.filter(column__in=column_ids).order_by('task_order')
            try:
                serialized_tasks = serializers.serialize('json', tasks)
            except:
                serialized_tasks = serializers.serialize('json', [tasks])
        except models.Task.DoesNotExist:
            serialized_tasks = []

        template_name = 'project_management/column.html'
        context = {
            "board": board,
            "columns": serialized_columns,
            "columnSet": json.loads(serialized_columns),
            "tasks": serialized_tasks
        }
        return render(request, template_name, context)


def get_task(request, restID):
    """
    Get task card
    """
    if request.method == "GET":
        task = models.Task.objects.get(restID=restID)
        serialized_task = serializers.serialize('json', [task], use_natural_foreign_keys=True, use_natural_primary_keys=True)

        data = {
            "task": serialized_task
        }



        return JsonResponse(data=data, content_type="application/json")
    
@login_required
def delete_task(request):
    if request.method == 'POST':
        data = request.POST
        task = models.Task.objects.get(restID=data.get("taskID"))

        models.Task.objects.filter(column=task.column, task_order__gt=task.task_order).update(task_order = F("task_order") - 1)
        task.delete()

        return JsonResponse({}, content_type="application/json")
    
    return JsonResponse({})