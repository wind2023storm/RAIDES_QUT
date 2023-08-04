from functools import wraps
from http import HTTPStatus

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.gis.geos import GEOSGeometry, Polygon, MultiPolygon, Point
from django.db import transaction
from django.db.models import Prefetch, Subquery, OuterRef, QuerySet, Count
from django.http import JsonResponse, HttpResponseNotFound, HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import resolve, reverse
from django.views import View
from django.db.models import F, ExpressionWrapper, DurationField
from django.contrib.gis.db.models.functions import Centroid
from django.template.loader import render_to_string
from django.core.mail import EmailMessage

import media_file
from lms.forms import *
from main.utils.query_analyze import django_query_analyze
from media_file.forms import CreateMultipleMediaFileForm
from notification.models import Notification
from notification.utils.utils import notify_users, notify_project_members
from project.models import Project, Permission, ProjectMember
from project.utils.decorators import has_project_permission
from lms.utils.feature_collection import get_feature_collection_from_project_parcels, get_feature_from


def create_debug_objects(request, project):
    """Creates some LandParcelProjects for debug purposes. Mostly for adding geometry to a model."""
    Parcel.objects.all().delete()

    def M(geom):
        if isinstance(geom, Polygon):
            geom = MultiPolygon([geom])

        return geom

    # Parcel
    new_parcels = [
        Parcel(feature_name="a", lot=73, plan="GEORGE", tenure="Beetles", geometry=M(
                GEOSGeometry(
                    '{"type": "Polygon", "coordinates": [ [ [ 152.802046115000053, -27.371197363999954 ], '
                    '[ 152.802128377000031, -27.371642565999935 ], [ 152.80042878800009, -27.372242642999936 ], '
                    '[ 152.800253558000122, -27.372314421999931 ], [ 152.800342026000067, -27.371760157999972 ], '
                    '[ 152.800975660000063, -27.371536491999962 ], [ 152.801704268000094, -27.371277628999962 ], '
                    '[ 152.802046115000053, -27.371197363999954 ] ] ]}'
                )
            )
               ),
        Parcel(feature_name="b", lot=42, plan="POTATO", tenure="Starch Free", geometry=M(
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

    Parcel.objects.bulk_create(new_parcels)

    # We don't do this with bulk create since bulk create bypasses the save method and won't run signals
    for parcel in Parcel.objects.all():
        ProjectParcel.objects.create(parcel=parcel, project=project, user_updated=request.user)

TEMPLATE = 'lms/'

@has_project_permission()
def lms_project(request, project, slug):
    """Base LMS View for a project. Pass forms and other project specific context here.
    To retrieve project parcels/owners utilize the ProjectView instead"""

    ProjectParcel.objects.bulk_create_for_project(project)
    # create_debug_objects(request, project)

    # Fetch the project parcels and related information.r.

    project_parcels = ProjectParcel.objects.lms_filter(project=project)
    feature_collection = get_feature_collection_from_project_parcels(project_parcels=project_parcels)

    context = {
        'project': project,
        'member': project.request_member[0],
        'owner_form': ParcelOwnerForm(request, project),
        'relationship_form': ParcelOwnerRelationshipForm(request, project),
        'modify_relationship_form': ParcelOwnerRelationshipForm(request, project, is_modify=True),
        'note_form': LandOwnerNoteForm(request, project),
        'correspondence_form': LandOwnerCorrespondenceForm(request, project),
        'task_form': LandOwnerTaskForm(request, project),
        'reminder_form': LandParcelOwnerReminderForm(request, project),
        'file_form': CreateMultipleMediaFileForm(),

        'parcels_feature_collection': json.dumps(feature_collection, default=str)
    }

    return render(request, TEMPLATE + '/base.html', context)


class LmsView(LoginRequiredMixin, View):
    """Abstract view class for usage in the LMS. """
    template_name = 'lms/base.html'
    url_name = ''
    """URL Name of url from Django URL"""
    action = ''
    project: Project
    """Current Project"""

    member: ProjectMember
    """Current user as Project Member"""

    project_parcels: ParcelProjectManager
    """Project Parcels of Current Project"""

    permission = Permission.READ
    post_permission = Permission.WRITE

    form_errors = None
    instance = None
    queryset = []

    @classmethod
    def as_view(cls, **kwargs):
        # Set up the permission from the urls.py
        cls.permission = kwargs.get('permission', cls.permission)
        cls.post_permission = kwargs.get('post_permission', cls.post_permission)

        return super().as_view(**kwargs)

    def pre_dispatch(self, request, *args, **kwargs):
        """Performs some additional setup before the HTTP method is dispatched. Typically used for initialising the
        views queryset or instance objects."""
        pass

    def dispatch(self, request, *args, **kwargs):
        """Sets up the project, and if the user exists in the project with the correct permissions, raises ObjectDoesNotExist"""
        self.url_name = resolve(self.request.path_info).url_name

        # Print some debug information about the view. TODO: Remove this when happy
        print(f'{request.scheme.upper()} {request.method} {self.__class__.__name__}("{self.url_name}") : {kwargs}\n\t{request.POST if request.POST else request.GET}')

        try:
            slug = kwargs.get('slug')
            self.action = kwargs.get('action')

            # Use the correct permission for the request type. Fallback on default if post not exist
            permission = self.post_permission if self.post_permission and request.POST else self.permission

            # Retrieve the project and members
            self.member = ProjectMember.objects.select_related('project').get(project__slug=slug, user=self.request.user, permission__gte=permission)
            self.project = self.member.project
            self.project_parcels = ProjectParcel.objects.lms_filter(project=self.project).annotate(middle_point=Centroid('parcel__geometry'))

            # Setup the base queryset
            self.pre_dispatch(request, *args, **kwargs)

        except ObjectDoesNotExist as e:
            print('dispatch(ObjectDoesNotExist)', e)
            return HttpResponse('Resource not found or user has insufficient privileges.', status=HTTPStatus.NOT_FOUND)
        except Exception as e:
            print('dispatch(Exception)', e)
            return HttpResponse(e, status=HTTPStatus.NOT_FOUND)

        return super().dispatch(request, *args, **kwargs)

    def render_view_template(self):
        """Renders the views template using the view as an input argument to the template"""
        return render_to_string(self.template_name, {'view': self}, request=self.request)

    def render_json_response(self):
        """Returns the default rendered JsonResponse with an OK status"""
        return JsonResponse({'html': self.render_view_template()}, status=HTTPStatus.OK)

    def get(self, request, *args, **kwargs):
        """Handles the views GET request response"""
        return self.render_json_response()

    def post(self, request, *args, **kwargs):
        """Handles the views POST request response"""
        return JsonResponse({}, status=HTTPStatus.NOT_IMPLEMENTED)


class ProjectView(LmsView):
    template_name = TEMPLATE + 'project.html'
    owners = []

    def pre_dispatch(self, request, *args, **kwargs):
        self.owners = ParcelOwner.objects.filter(project=self.project)

class MapView(LmsView):

    def get(self, request, *args, **kwargs):
        print(kwargs.get('parcel'))
        selected_parcel_feature = None

        for project_parcel in self.project_parcels:
            # Selected feature
            if project_parcel.id == kwargs.get('parcel'):
                selected_parcel_feature = get_feature_from(project_parcel, middle_point=json.loads(project_parcel.middle_point.json))
                break
                
        
        feature_collection = get_feature_collection_from_project_parcels(project_parcels=self.project_parcels)
        
        responseData = {
            "data": {
                "selectedFeature": selected_parcel_feature,
                "parcels_feature_collection": feature_collection
            }
        }

        return JsonResponse(data=responseData)


class ParcelView(LmsView):
    template_name = TEMPLATE + 'parcel.html'

    def pre_dispatch(self, request, *args, **kwargs):

        if self.url_name == 'parcel':
            parcel_id = self.kwargs.get('parcel', None)

            # Since we're likely going to be displaying more information about an individual parcel,
            # prefetch as much information about it as we can.
            # TODO: Fix problem query a single parcel
            # self.instance = ProjectParcel.objects \
            #     .select_related('parcel') \
            #     .prefetch_related(
            #         Prefetch('owners', queryset=ParcelOwnerRelationship.objects.select_related('owner')))\
            #     .annotate(mail_targets=Count('owners'))\
            #     .get(id=parcel_id, project=self.project) 
            
            self.instance = ProjectParcel.objects \
                .lms_filter(project=self.project) \
                .annotate(mail_targets=Count('owners'))\
                .get(id=parcel_id, project=self.project)

        elif self.url_name == 'parcels':
            self.queryset = ProjectParcel.objects\
                .lms_filter(project=self.project) \
                .prefetch_related('owners')\
                .annotate(
                    mail_targets=Count('owners')
                )
        else:
            raise ObjectDoesNotExist()

    def post(self, request, *args, **kwargs):
        return JsonResponse({}, status=HTTPStatus.NOT_IMPLEMENTED)


class RelationshipView(LmsView):
    """Handles GET and POST requests regarding a ParcelOwnerRelationship."""
    template_name = TEMPLATE + 'owner_relationship.html'
    parcel: ProjectParcel = None
    owner: ParcelOwner = None

    def pre_dispatch(self, request, *args, **kwargs):
        parcel_id = kwargs.get('parcel', None)
        relationship_id = kwargs.get('relationship', None)

        if self.url_name:
            self.queryset = ParcelOwnerRelationship.objects\
                .select_related('parcel', 'owner')\
                .filter(parcel_id=parcel_id, parcel__project=self.project, owner__project=self.project)\
                .annotate(
                    parcel_count=Count('owner__parcels', distinct=True),
                    note_count=Count('owner__notes', distinct=True),
                    correspondence_count=Count('owner__correspondence', distinct=True),
                    task_count=Count('owner__tasks', distinct=True),
                    reminder_count=Count('owner__reminders', distinct=True),
                    file_count=Count('owner__files', distinct=True),
                    duration=ExpressionWrapper(F('date_ownership_ceased') - F('date_ownership_start'), output_field=DurationField())
                ).order_by(
                    '-is_mail_target',  
                    '-date_ownership_start',  
                    '-duration'
                )
            self.form_instance = ParcelOwnerRelationshipForm(request, self.project)

        if self.url_name in ['relationship', 'modify_relationship']:
            self.instance = ParcelOwnerRelationship.objects \
                .select_related('parcel', 'owner') \
                .get(id=relationship_id, parcel_id=parcel_id, parcel__project=self.project, owner__project=self.project)
            self.parcel = self.instance.parcel
            self.owner = self.instance.owner

        elif self.url_name == 'relationships':
            if request.POST:
                self.parcel = ProjectParcel.objects.lms_filter(project=self.project).get(id=parcel_id, project=self.project)

        elif self.url_name == 'delete_relationship':
            self.instance = ParcelOwnerRelationship.objects\
                .get(id=relationship_id, parcel_id=parcel_id, parcel__project=self.project, owner__project=self.project)

    def post(self, request, *args, **kwargs):

        self.form_errors = {}

        if self.url_name in ['relationships', 'modify_relationship']:

            # In the instance we are using the form which allows us to create an owner and relationship at the same time
            # we need to have created the owner first since the relationship relies on an existing owner.
            if not self.owner and 'owner' not in request.POST:
                owner_form = ParcelOwnerForm(request, project=self.project, data=request.POST or None)

                if owner_form.is_valid():
                    self.owner = owner_form.save()
                else:
                    self.form_errors.update(owner_form.errors)

            # Attempt to create/modify the relationship
            relationship_form = ParcelOwnerRelationshipForm(request, instance=self.instance, project=self.project, owner=self.owner, parcel=self.parcel, data=request.POST or None)

            # Modify the model
            if relationship_form.is_valid():
                self.instance = relationship_form.save()
                self.form_instance = relationship_form
            else:
                self.form_errors.update(relationship_form.errors)

        elif self.url_name == 'delete_relationship':
            self.instance.delete()

        if self.form_errors:
            return JsonResponse(self.form_errors, status=HTTPStatus.BAD_REQUEST)

        return self.render_json_response()



class OwnerView(LmsView):
    """
        Handles GET and POST requests regarding a ParcelOwner

        TEMPLATE REQUIRED VARIABLES:
        - self.instance: to fetch for owner view
        - self.queryset: to fetch for list of owners    
    """

    template_name = TEMPLATE + 'owner.html'


    OWNER_ANNOTATIONS = {
        'parcel_count': Count('parcels', distinct=True),
        'note_count': Count('notes', distinct=True),
        'correspondence_count': Count('correspondence', distinct=True),
        'task_count': Count('tasks', distinct=True),
        'reminder_count': Count('reminders', distinct=True),
        'file_count': Count('files', distinct=True),
    }

    owner_parcel_relationships = []
    """(`ParcelOwnerRelationship`) Relationships between one ParcelOwner and ParcelOwnerRelationship"""

    owner_parcels_feature_collection = []
    """Geo Feature Collection for Owner Parcels """


    def pre_dispatch(self, request, *args, **kwargs):

        owner_id = kwargs.get('owner', None)

        if self.url_name:
            self.queryset = ParcelOwner.objects.filter(project=self.project)\
                .annotate(**self.OWNER_ANNOTATIONS)


        if self.url_name in ['owner', 'modify_owner', 'delete_owner']:
            self.instance = ParcelOwner.objects.prefetch_related(
                'files',
                'notes',
                'correspondence',
                'tasks',
                'reminders',
                'history_relation',
            ).annotate(
                **self.OWNER_ANNOTATIONS
            ).get(id=owner_id, project=self.project)

            relationships = self.instance.parcel_relationships.all()

            owner_project_parcels = [relationship.parcel for relationship in relationships]
            feature_collection = get_feature_collection_from_project_parcels(owner_project_parcels)

            self.owner_parcel_relationships = relationships
            self.owner_parcels_feature_collection = json.dumps(feature_collection, default=str)

    def post(self, request, *args, **kwargs):

        if self.url_name in ['owners', 'modify_owner']:
            form = ParcelOwnerForm(request, instance=self.instance, project=self.project, data=request.POST or None)

            # Create the model
            if form.is_valid():
                self.instance = form.save()

                if request.FILES:
                    file_form = CreateMultipleMediaFileForm(
                        instance=self.instance,  # Change this to model with 'files' field
                        files=request.FILES,
                        tag=ParcelOwnerForm.FILE_TYPE,
                        allowed_extensions=ParcelOwnerForm.ALLOWED_EXTENSIONS
                    )

                    if file_form.is_valid():
                        file_form.save()
                    else:
                        self.form_errors.update(file_form.errors)

                self.instance = ParcelOwner.objects.prefetch_related(
                    'files',
                    'notes',
                    'correspondence',
                    'tasks',
                    'reminders',
                    'history_relation',
                ).annotate(
                    **self.OWNER_ANNOTATIONS
                ).get(id=self.instance.id, project=self.project)
            else:
                self.form_errors = form.errors

        elif self.url_name == 'delete_owner':
            try:
                self.instance.delete()
            except Exception as e:
                return JsonResponse({}, status=HTTPStatus.BAD_REQUEST)
            else:
                return JsonResponse({}, status=HTTPStatus.OK)

        if self.form_errors:
            return JsonResponse(self.form_errors, status=HTTPStatus.BAD_REQUEST)

        return self.render_json_response()


class FilesView(LmsView):
    template_name = TEMPLATE + 'owner_files.html'
    model = MediaFile
    FILE_TYPE = MediaFile.DOCUMENT
    ALLOWED_EXTENSIONS = MediaFile.Extensions.DOCUMENT + MediaFile.Extensions.PDF + MediaFile.Extensions.EXCEL + MediaFile.Extensions.DATA + MediaFile.Extensions.IMAGE
    owner = None

    def pre_dispatch(self, request, *args, **kwargs):
        owner_id = kwargs.get('owner', None)
        file_id = kwargs.get('file', None)

        self.owner = ParcelOwner.objects.prefetch_related('files').annotate(files_count=Count("files")).get(id=owner_id, project=self.project)

        if self.url_name in ['file', 'download_file'] or self.url_name == 'delete_file':
            self.instance = self.owner.files.get(id=file_id)

        elif self.url_name == 'files':
            self.queryset = self.owner.files.all()

            print(self.queryset)

    def get(self, request, *args, **kwargs):

        if self.url_name == 'download_file':
            return self.instance.to_file_response()

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if self.url_name == 'files' and request.FILES:
            file_form = CreateMultipleMediaFileForm(
                instance=self.owner,  # Change this to model with 'files' field
                files=request.FILES,
                tag=self.FILE_TYPE,
                allowed_extensions=self.ALLOWED_EXTENSIONS
            )

            if file_form.is_valid():
                self.queryset = file_form.save()

        elif self.url_name == 'delete_file':
            self.instance.delete()

        return self.render_json_response()


class InfoView(LmsView):
    template_name = ''
    model = None
    form = None
    name = ''
    owner = None

    def pre_dispatch(self, request, *args, **kwargs):
        owner_id = kwargs.get('owner', None)
        instance_id = kwargs.get(self.name, None)

        self.owner = ParcelOwner.objects.get(id=owner_id, project=self.project)

        if self.url_name:
            self.queryset = self.model.objects.filter(owner=self.owner)

        if self.url_name in [self.name, f'modify_{self.name}', f'delete_{self.name}']:
            self.instance = self.model.objects.get(id=instance_id, owner=self.owner)

    def post(self, request, *args, **kwargs):

        if self.url_name in [f'{self.name}s', f'modify_{self.name}']:
            form = self.form(request, instance=self.instance, owner=self.owner, project=self.project, data=request.POST or None)
            # Modify the model
            if form.is_valid():
                self.instance = form.save()

                if request.FILES and hasattr(self.instance, 'files'):
                    model_file_form = CreateMultipleMediaFileForm(
                        instance=self.instance,  # Change this to model with 'files' field
                        files=request.FILES,
                        tag=self.form.FILE_TYPE,
                        allowed_extensions=self.form.ALLOWED_EXTENSIONS
                        )

                    if model_file_form.is_valid():
                        model_file_form.save()
                    else:
                        self.form_errors.update(model_file_form.errors)

            else:
                self.form_errors = form.errors
        elif self.url_name == f'delete_{self.name}':
            self.instance.delete()

        if self.form_errors:
            return JsonResponse(self.form_errors, status=HTTPStatus.BAD_REQUEST)

        return self.render_json_response()


class NoteView(InfoView):
    template_name = TEMPLATE + 'owner_notes.html'
    model = LandParcelOwnerNote
    form = LandOwnerNoteForm
    name = 'note'
            

class TaskView(InfoView):
    template_name = TEMPLATE + 'owner_tasks.html'
    model = LandParcelOwnerTask
    form = LandOwnerTaskForm
    name = 'task'


class CorrespondenceView(InfoView):
    template_name = TEMPLATE + 'owner_correspondence.html'
    model = LandParcelOwnerCorrespondence
    form = LandOwnerCorrespondenceForm
    name = 'correspondence'

    def pre_dispatch(self, request, *args, **kwargs):
        super().pre_dispatch(request, *args, **kwargs)
        file_id = kwargs.get('file', None)

        instance_id = kwargs.get(self.name, None)

        if (instance_id):
            self.instance = self.model.objects.get(id=instance_id, owner=self.owner)

        if self.url_name == 'correspondence_download_file':
            self.correspondence_file = self.instance.files.get(id=file_id)
    
    def get(self, request, *args, **kwargs):
        if (self.url_name == 'correspondence_download_file'):
            return self.correspondence_file.to_file_response()
        return super().get(request, *args, **kwargs)

class ReminderView(InfoView):
    template_name = TEMPLATE + 'owner_reminders.html'
    model = LandParcelOwnerReminder
    form = LandParcelOwnerReminderForm
    name = 'reminder'


class HistoryView(LmsView):
    """Handles GET and POST requests regarding a ParcelOwner"""

    template_name = TEMPLATE + 'history.html'
    model = ''

    def pre_dispatch(self, request, *args, **kwargs):
        self.model = kwargs.get('model', None)

        object_id = kwargs.get('object', None)
        history_id = kwargs.get('history', None)

        # Have to discover where our project is with respect to the incoming model
        # Yeah it's disgusting but at least the urls.py isn't cluttered with different routes for each model.
        obj_dict = {
            'owner': {
                'object': ParcelOwner,
                'project': 'project',
            },
            'parcel': {
                'object': ProjectParcel,
                'project': 'project',
            },
            'relationship': {
                'object': ParcelOwnerRelationship,
                'project': 'owner__project',
            },
        }.get(self.model, None)

        project_query_dict = {obj_dict['project']: self.project}

        obj_model = obj_dict['object']
        obj_history = obj_model.objects.get(id=object_id, **project_query_dict).history_relation

        if self.url_name in ['history', 'revert_history']:
            self.instance = obj_history.get(id=history_id)

        elif self.url_name == 'histories':
            self.queryset = obj_history.all()

    def post(self, request, *args, **kwargs):
        if self.url_name in ['revert_history']:
            self.instance.revert_to_here()

        return self.render_json_response()
    
class MailView(RelationshipView):
    """
        GET: Return a list of mail targets relationship (ParcelRelationship)
        POST: Send bulk email to mail targets of parcel

        POST request data: 
            mail_targets: array of id string of selected mail targets
            mail_subject: string
            mail_body: string
    """

    # self.queryset: ParcelOwnerRelationship

    template_name = TEMPLATE + 'parcel_mail_modal.html'

    def pre_dispatch(self, request, *args, **kwargs):
        super().pre_dispatch(request, *args, **kwargs)

        parcel_id = kwargs.get('parcel', None)
    
        # self.queryset = self.queryset.filter(is_mail_target=True)
        self.parcel = ProjectParcel.objects.lms_filter(project=self.project).get(id=parcel_id, project=self.project)

    def post(self, request, *args, **kwargs):
        default_mail_subject = f'Mail From Parcel {self.parcel.parcel.lot_plan}'

        print('Request POST', request.POST)
        post_data = request.POST
        
        # Array of ID of selected mail targets
        mail_targets_list_data = json.loads(post_data.get('mail_targets', '[]'))
        mail_subject = post_data.get('mail_subject', default_mail_subject)
        mail_body = post_data.get('mail_body')

        if mail_subject.strip() == "":
            mail_subject = default_mail_subject

        mail_targets_owners = self.queryset.filter(id__in=mail_targets_list_data)

        receivers_list = []
        for relationship in mail_targets_owners:
            if (relationship.owner.contact_email is not None):
                receivers_list.append(relationship.owner.contact_email)
            
        print('sending list', receivers_list)
        # receivers_list = ['johnny@orefox.com', 'test1@gmail.com']

        body = render_to_string("lms/mail_template/parcel_bulk_mail.html", {
            "protocol": 'https' if request.is_secure() else 'http',
            "project_parcel": self.parcel,
            "content": mail_body
        })
        
        email = EmailMessage(subject=mail_subject, body=body, to=receivers_list)
        email.content_subtype = 'html'

        for fileKey, fileValue in request.FILES.lists():
            emailFile = fileValue[0]
            email.attach(emailFile.name, emailFile.read(), emailFile.content_type)

        if email.send():
            return JsonResponse(data={'status': 200}, status=200)
        
        print(','.join(receivers_list))
        return JsonResponse(data={
            'error': 'Unable to send bulk email to ' + ','.join(receivers_list)
        }, status=404)
# 
# 
# class HistoryView(LmsView):
#     template_name = 'lms/parcel_history.html'
#     model = None
#     form_class = None
# 
#     action_permissions = {
#         'get': Permission.READ,
#         'revert': Permission.ADMIN,
#     }
# 
#     def _get_owner_query_dict(self):
#         return {
#             'id': self.request.GET.get('history') or self.request.POST.get('history'),
#             'target_id': self.request.GET.get('owner') or self.request.POST.get('owner'),
#             'target__parcels__project_id': self.project.id
#         }
# 
#     def _get_parcel_query_dict(self):
#         return {
#             'id': self.request.GET.get('history') or self.request.POST.get('history'),
#             'target_id': self.request.GET.get('parcel') or self.request.POST.get('parcel'),
#             'target__project_id': self.project.id
#         }
# 
#     def _call_before(self, *args, **kwargs):
#         """Changes the model and _get_query_dict functions depending on the model passed through the original view
#         argument"""
#         # Could have easily split the view in two for the different models, but since they perform the same thing it
#         # just felt easier to handle this before the view is called. We're still able to validate whether the URL
#         # argument is correct anyway.
#         model = kwargs.get('model')
# 
#         if model == 'owner':
#             self.model = LandParcelOwnerHistory
#             self._get_query_dict = self._get_owner_query_dict
#         elif model == 'parcel':
#             self.model = LandParcelHistory
#             self._get_query_dict = self._get_parcel_query_dict
#         else:
#             raise ValidationError("Invalid Model")
# 
#     @lms_has_permission(call_before='_call_before')
#     def post(self, request, action, *args, **kwargs):
#         """The only post request action handleable by history is a reversion which requires admin privileges."""
#         if action != 'revert':
#             return JsonResponse({}, status=HTTPStatus.BAD_REQUEST)
# 
#         try:
#             instance = self._get_instance()
#         except ObjectDoesNotExist:
#             return JsonResponse({}, status=HTTPStatus.NOT_FOUND)
#         else:
#             instance.revert_to_here()
# 
#         # Handle Project Notification
#         notify_project_members(
#             project=self.project,
#             user_from=self.request.user,
#             summary=f"{self.model._meta.verbose_name.title()} <b>{instance}</b> was rolled back by <b>{self.request.user}</b> to {instance.date_created}.",
#             target=instance,
#             url=reverse('lms:project', kwargs={'slug': self.project.slug})
#         )
# 
#         return JsonResponse(self._render_queryset([instance]), status=HTTPStatus.OK)
#


# class NoteView(LmsView):
#     template_name = 'lms/owner_notes.html'
#     model = LandParcelOwnerNote
#     form_class = LandOwnerNoteForm
#
#     def _get_query_dict(self):
#         return {
#             'id': self.request.POST.get('note', None) or self.request.GET.get('note', None),
#             'owner': self.request.POST.get('owner', None) or self.request.GET.get('owner', None),
#             'owner__parcels__project': self.project
#         }
#
#
# class CorrespondenceView(LmsView):
#     template_name = 'lms/owner_correspondence.html'
#     model = LandParcelOwnerCorrespondence
#     form_class = LandOwnerCorrespondenceForm
#
#     def _get_query_dict(self):
#         return {
#             'id': self.request.POST.get('correspondence', None) or self.request.GET.get('correspondence', None),
#             'owner': self.request.POST.get('owner', None) or self.request.GET.get('owner', None),
#             'owner__parcels__project': self.project
#         }
#
#
# class ReminderView(LmsView):
#     template_name = 'lms/owner_reminders.html'
#     model = LandParcelOwnerReminder
#     form_class = LandParcelOwnerReminderForm
#
#     def _get_query_dict(self):
#         return {
#             'id': self.request.POST.get('reminder', None) or self.request.GET.get('reminder', None),
#             'owner': self.request.POST.get('owner', None) or self.request.GET.get('owner', None),
#             'owner__parcels__project': self.project
#         }
#
#
# class TaskView(LmsView):
#     template_name = 'lms/owner_tasks.html'
#     model = LandParcelOwnerTask
#     form_class = LandOwnerTaskForm
#
#     def _get_query_dict(self):
#         return {
#             'id': self.request.POST.get('task', None) or self.request.GET.get('task', None),
#             'owner': self.request.POST.get('owner', None) or self.request.GET.get('owner', None),
#             'owner__parcels__project': self.project
#         }
# 
# class FileView(LmsView):
#     template_name = 'lms/files.html'  # Not set up in similar fashion to other templates yet
#     model = MediaFile
# 
#     action_permissions = {
#         # 'get': Permission.READ,  # Uncomment when this is created. Check get() for more details
#         'download': Permission.READ,
#         'delete': Permission.ADMIN,
#     }
# 
#     def _call_before(self, *args, **kwargs):
#         """Get the media file for handling respective requests"""
#         try:
#             file_id = kwargs.get('file_id')
#             self.media_file = self.model.objects.get(id=file_id, land_parcel_files__project=self.project)
#         except ObjectDoesNotExist:
#             raise ValidationError
# 
#     @lms_has_permission()
#     def get(self, request, *args, **kwargs):
#         if self.action == 'get':
#             # Complex logic required as many LMS models have a file directory. This would take some
#             # additional layered querying similar to the HistoryView
#             raise NotImplementedError()
# 
#         elif self.action == 'download':
#             return self.media_file.to_file_response()
#         else:
#             return JsonResponse({}, status=HTTPStatus.BAD_REQUEST)
# 
#     @lms_has_permission()
#     def post(self, request, *args, **kwargs):
#         try:
#             self.media_file.delete()
#         except Exception:
#             return JsonResponse({}, status=HTTPStatus.BAD_REQUEST)
#         else:
#             # Handle Project Notification
#             notify_project_members(
#                 project=self.project,
#                 user_from=self.request.user,
#                 summary=f"The file <b>{self.media_file}</b> was deleted by <b>{self.request.user}</b>.",
#                 url=reverse('lms:project', kwargs={'slug': self.project.slug})
#             )
# 
#             return JsonResponse({'id': kwargs.get('file_id')}, status=HTTPStatus.OK)
