import datetime

from http import HTTPStatus
from typing import Union
from django.contrib.auth import get_user_model
from django.core.handlers.wsgi import WSGIRequest
from django.test import Client, TestCase, RequestFactory
from django.urls import reverse
from django.views import View
import uuid
from django.contrib.gis.db import models

from lms.views import LmsView, OwnerView, RelationshipView, InfoView, NoteView, CorrespondenceView, ReminderView, TaskView
from lms.models import Parcel, ProjectParcel, ParcelOwner, ParcelOwnerRelationship, LandParcelOwnerNote, LandParcelOwnerCorrespondence, LandParcelOwnerReminder, LandParcelOwnerTask
from project.models import Permission, Project, ProjectMember
from lms.views import lms_project, ProjectView
from lms.tests import dummy_parcels



User = get_user_model()


class LMSViewTestCase(TestCase):

    url = '/'
    request_factory = RequestFactory()
    client = Client()

    logged_in_user = None
    """
        Used for auth request and response

        If you want to change, define it in setUp()

        ----

        def setUp(self):
            super().setUp()
            self.logged_in_user = self.u1
    """

    def setUp(self):
        """
        Set up LMS data:
        - su, u1, u2, u3 
        - project1
        - parcel id 1, id 2
        - projects parcels (id 1, id 2)
        - first_owner (for project1)
        """

        self.su = User.objects.create_superuser('admin@email.com', 'admin', first_name='Mein', last_name='Luftkissenfahrzeug')
        self.logged_in_user = self.su

        self.u1 = User.objects.create_user('user1@email.com', 'pass', first_name='George', last_name='Costanza')
        self.u2 = User.objects.create_user('user2@email.com', 'pass', first_name='Ronald', last_name='Weasley')
        self.u3 = User.objects.create_user('user3@email.com', 'pass', first_name='Hubert', last_name='Cumberdale')
        
        self.project1 = Project.objects.create(**{
            'name': 'Owner Project',
            'owner': self.su,
            'objective': 'owner test',
            'locality': 'someplace neat',
            'credits': 12345
        })
        ProjectMember.objects.create(project=self.project1, user=self.su, permission=Permission.ADMIN)
        ProjectMember.objects.create(project=self.project1, user=self.u1, permission=Permission.WRITE)
        ProjectMember.objects.create(project=self.project1, user=self.u2, permission=Permission.READ)
        ProjectMember.objects.create(project=self.project1, user=self.u3, permission=Permission.ADMIN)

        Parcel.objects.bulk_create(dummy_parcels)

        for index, parcel in enumerate(Parcel.objects.all()):
            ProjectParcel.objects.create(id=uuid.UUID(int=index+1), parcel=parcel, project=self.project1, user_updated=self.su)

        self.first_owner = ParcelOwner.objects.create(id=uuid.UUID(int=1), first_name='Johnny', last_name='Nguyen', project=self.project1, user_created=self.su, user_updated=self.su)

    def auth_request(self, url_string: str):
        """
            Set user for GET Request Factory

            Default User: self.su
        """
        request = self.request_factory.get(url_string)
        request.user = self.logged_in_user

        return request
    
    def auth_post_request(self, url_string: str, data):
        """
            Set user for POST Request Factory

            Default User: self.su
        """
        request = self.request_factory.post(url_string, data)
        request.user = self.logged_in_user

        return request
    
    def auth_response(self, url_name: str, user = None):
        """
        Login user for Client response
        Default User: self.su
        """
        self.client.force_login(self.logged_in_user)
        return self.client.get(url_name)
    
    def auth_post_response(self, url_name: str, data):
        self.client.force_login(self.logged_in_user)
        return self.client.post(url_name, data)
    

    def setUp_view(self, view: LmsView, request: WSGIRequest, *args, **kwargs):
        """
        Mimic ``as_view()``, but returns view instance.
        Use this function to get view instances on which you can run unit tests,
        by testing specific methods.

        Function will run setup() -> dispatch()
        """

        view.request = request
        view.args = args
        view.kwargs = kwargs

        view.setup(request, **kwargs)
        view.dispatch(request, **kwargs)

        return view
    
    def setUp_auth_view(self, view: LmsView, url_string: str, *args, **kwargs):
        """
        Log in user `self.logged_in_user` through Request Factory, then perform View setup() and dispatch()
        
        `Example`: self.setUp_auth_view(LmsView(), url_string, **kwrags) 
        """
        request = self.auth_request(url_string)
        view = self.setUp_view(view, request, *args, **kwargs)

        return view
    
    def setUp_post_auth_view(self, view: LmsView, url_string: str, data, *args, **kwargs):
        """
        Log in user `self.logged_in_user` through Request Factory, then perform View setup() and dispatch()
        """
        request = self.auth_post_request(url_string, data)
        view = self.setUp_view(view, request, *args, **kwargs)

        return view



    def tearDown(self) -> None:
        return super().tearDown()
    
class LMSProjectTesCase(LMSViewTestCase):
    def test_get_base_no_user(self):
        url = reverse('lms:lms', args=[self.project1.slug])
        request = self.request_factory.get(url)
        response = self.client.get(url)

        self.assertFalse(hasattr(request, 'user'))
        if (hasattr(request, 'user')):
            self.assertIsNone(request.user)

        self.assertIsNot(response.status_code, HTTPStatus.OK, 'As no user login, the url is not accessed')

        
    
    def test_get_base(self):
        """
            Test response of base of lMS
        """
        url = reverse('lms:lms', args=[self.project1.slug])
        request = self.auth_request(url)
        response = self.auth_response(url)

        self.assertTrue(hasattr(request,'user'))
        if (hasattr(request, 'user')):
            self.assertIsNotNone(request.user)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response=response, template_name='lms//base.html')

        context = response.context
        self.assertIsNotNone(context['project'])
        project = context['project']
        self.assertEqual(project.id, self.project1.id)

        self.assertIsNotNone(context['member'])


    def test_lms_view_class(self):
        """Test LMSView. Include: dispatch()"""
        url = reverse('lms:project', args=[self.project1.slug])
        request = self.auth_request(url)
        # response = self.auth_response(url)
        # view = self.setup_view(LmsView(), request=request)

        view2 = ProjectView()
        view2.setup(request, slug=self.project1.slug)
        view2.dispatch(request, slug=self.project1.slug)
        
        self.assertNotEqual(view2.url_name, '')
        self.assertIsNotNone(view2.project)

class OwnerViewTestCase(LMSViewTestCase):

    def setup_owners_or_onwer_view(self, viewname: str, owner_id: uuid.UUID = None, project: Project = None):
        """
        Set up for OwnerView

        Return: OwnerView
        """
        project = self.project1 if project is None else project
        if (owner_id is None):
            kwargs = {'slug': project.slug}
        else:
            kwargs = {'slug': project.slug, 'owner': owner_id}
        
        print(__name__, 'kwargs', kwargs)
        url = reverse(viewname, kwargs=kwargs)
        request = self.auth_request(url)

        view: OwnerView = self.setUp_view(OwnerView(), request, **kwargs)

        return view
    
    def setup_post_owner_view(self, viewname: str, data, project: Project = None):
        project = self.project1 if project is None else project
        url = reverse(viewname, kwargs={'slug': project.slug})
        request = self.auth_post_request(url, data)

        view = self.setUp_view(OwnerView(), request, slug=project.slug)
        return view
    
    def post_owner_view(self, viewname: str, data, project: Project = None):
        project = self.project1 if project is None else project
        url = reverse(viewname, kwargs={'slug': project.slug})
        request = self.auth_post_request(url, data)

        view = self.setUp_view(OwnerView(), request, slug=project.slug)

        return view.post(request, slug=project.slug)

    def test_get_owner__instance_queryset_exist(self):
        """
            Get an owner require view.instance and view.queryset for template
        """
        print('first owner id', self.first_owner.id)
        view = self.setup_owners_or_onwer_view('lms:owner', self.first_owner.id)

        self.assertIsNotNone(view.instance)
        self.assertIsNotNone(view.queryset)

    def test_get_multiple_owners__queryset_exists(self):
        url = reverse('lms:owners', kwargs={'slug': self.project1.slug})
        view = self.setup_owners_or_onwer_view('lms:owners')

        self.assertIsNotNone(view.queryset)

    def test_owner_view_post_owner__instance_exists(self):
        data = {
            'title': 0,
            'first_name': 'Test 1',
            'last_name': 'Test 1 last',
            'gender': 0
        }
        view = self.setup_post_owner_view('lms:owners', data)

        self.assertIsNotNone(view.instance)
        


    def test_owner_CRUD_operation(self):
        url_string = reverse('lms:owners', kwargs={'slug': self.project1.slug})
        data = {
            'title': 0,
            'first_name': 'Test 1',
            'last_name': 'Test 1 last',
            'gender': 0
        }
        request = self.auth_post_request(url_string, data)
        response = OwnerView.as_view()(request, slug=self.project1.slug)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(ParcelOwner.objects.filter(first_name='Test 1').exists())

        # View Owner
        owner = ParcelOwner.objects.get(first_name='Test 1')
        owner_kwargs = {'slug': self.project1.slug, 'owner': owner.id}
        url_string = reverse('lms:owner', kwargs=owner_kwargs)
        request = self.auth_request(url_string)
        response =  OwnerView.as_view()(request, **owner_kwargs)
        self.assertEqual(response.status_code, HTTPStatus.OK)

        view = self.setup_owners_or_onwer_view(viewname='lms:owner', owner_id=owner.id)

        self.assertIsNotNone(view.instance)
        self.assertEqual(view.instance.id, owner.id)

        # Update Owner
        url_string = reverse('lms:modify_owner', kwargs=owner_kwargs)
        data = {
            'title': 1,
            'first_name': 'Test 2',
            'last_name': 'Test 2 last',
            'gender': 0
        }
        request = self.auth_post_request(url_string, data=data)
        response =  OwnerView.as_view()(request, **owner_kwargs)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        
        owner = ParcelOwner.objects.get(id=owner.id)
        self.assertEqual(owner.title, 1)
        self.assertEqual(owner.first_name, 'Test 2')
        self.assertEqual(owner.last_name, 'Test 2 last')

        # Delete Onwer
        url_string = reverse('lms:delete_owner', kwargs={'slug': self.project1.slug, 'owner': owner.id})
        request = self.auth_post_request(url_string, data={})
        response = OwnerView.as_view()(request, slug=self.project1.slug, owner=owner.id)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFalse(ParcelOwner.objects.filter(first_name='Test 1').exists())


class RelationshipTestCase(LMSViewTestCase):
    """
    Test Case for Relationship View

    owner: self.first_owner
    """

    PROJECT_PARCEL: ProjectParcel = None

    def setUp(self):
        super().setUp()
        self.PROJECT_PARCEL = ProjectParcel.objects.get(id=uuid.UUID(int=1))
        self.first_relationship = ParcelOwnerRelationship.objects.create(
            parcel=self.PROJECT_PARCEL, 
            owner=self.first_owner,
            user_created=self.logged_in_user,
            user_updated=self.logged_in_user
            )


    def test_get__queryset_always_exist(self):
        # Get multiple relationships
        kwargs = {'slug': self.project1.slug, 'parcel': self.PROJECT_PARCEL.id}
        url_string = reverse('lms:relationships', kwargs=kwargs)
        view: RelationshipView = self.setUp_auth_view(RelationshipView(), url_string=url_string, **kwargs)
        self.assertIsNotNone(view.queryset)

        # Get single relationship
        kwargs = {**kwargs, 'relationship': self.first_relationship.id}
        url_string = reverse('lms:relationship', kwargs=kwargs)
        view = self.setUp_auth_view(RelationshipView(), url_string, **kwargs)
        
        self.assertIsNotNone(view.queryset)

        # Modify relationships
        url_string = reverse('lms:modify_relationship', kwargs=kwargs)
        view = self.setUp_post_auth_view(RelationshipView(), url_string, {}, **kwargs)
        self.assertIsNotNone(view.queryset)

        # Delete relationship
        url_string = reverse('lms:delete_relationship', kwargs=kwargs)
        view = self.setUp_post_auth_view(RelationshipView(), url_string, {}, **kwargs)
        self.assertIsNotNone(view.queryset)


    def test_get_single__instance_parcel_owner_exists(self):
        """
        When getting an instance, these variables are required for `view` in frontend:
        - instance
        - parcel
        - owner
        """
        kwargs = {'slug': self.project1.slug, 'parcel': self.PROJECT_PARCEL.id, 'relationship': self.first_relationship.id}
        url_string = reverse('lms:relationship', kwargs= {'slug': self.project1.slug, 'parcel': self.PROJECT_PARCEL.id, 'relationship': self.first_relationship.id})

        view: RelationshipView = self.setUp_auth_view(RelationshipView(), url_string, **kwargs)

        self.assertIsNotNone(view.instance)
        self.assertTrue(isinstance(view.instance, ParcelOwnerRelationship))

        self.assertIsNotNone(view.parcel)
        self.assertIsNotNone(view.owner)
        

    def test_CRUD(self):
        """
        Test CREATE, UPDATE, READ and DELETE OPERATIONS
        """
        new_owner = ParcelOwner.objects.create(first_name='Test 2', last_name='Test 2', project=self.project1, user_created=self.logged_in_user, user_updated=self.logged_in_user)

        #Create
        kwargs = {'slug': self.project1.slug, 'parcel': self.PROJECT_PARCEL.id}
        url_string = reverse('lms:relationships', kwargs=kwargs)
        data = {
            'parcel': self.PROJECT_PARCEL.id,
            'owner': new_owner.id,
            'date_ownership_start': datetime.date(2023, 1, 2),
            'date_ownership_ceased': datetime.date(2023, 2, 2)
        }

        request = self.auth_post_request(url_string, data=data)
        response = RelationshipView.as_view()(request, **kwargs)

        new_relationship = ParcelOwnerRelationship.objects.filter(parcel_id=self.PROJECT_PARCEL.id, owner_id=new_owner.id, parcel__project=self.project1)
        self.assertTrue(new_relationship.exists())
        new_relationship =  ParcelOwnerRelationship.objects.get(parcel_id=self.PROJECT_PARCEL.id, owner_id=new_owner.id, parcel__project=self.project1)

        self.assertTrue(response.status_code, HTTPStatus.OK)

        self.assertEqual(new_relationship.is_mail_target, False)
        self.assertEqual(new_relationship.date_ownership_start, datetime.date(2023, 1, 2))
        self.assertEqual(new_relationship.date_ownership_ceased, datetime.date(2023, 2, 2))

        # Read
        kwargs = {**kwargs, 'relationship': new_relationship.id}
        url_string = reverse('lms:relationship', kwargs=kwargs)
        
        view: RelationshipView = self.setUp_auth_view(RelationshipView(), url_string, **kwargs)
        
        self.assertEqual(view.instance.owner.id, new_owner.id)
        self.assertEqual(view.instance.parcel.id, self.PROJECT_PARCEL.id)


        # Modify
        url_string = reverse('lms:modify_relationship', kwargs=kwargs)
        data = {
            'parcel': self.PROJECT_PARCEL.id,
            'owner': new_owner.id,
            'date_ownership_start': datetime.date(2023, 4, 10),
            'date_ownership_ceased': datetime.date(2023, 5, 10)
        }
        
        request = self.auth_post_request(url_string, data)
        response = RelationshipView.as_view()(request, **kwargs)

        self.assertTrue(response.status_code, HTTPStatus.OK)


        self.assertEqual(view.instance.owner.id, new_owner.id)
        self.assertEqual(view.instance.parcel.id, self.PROJECT_PARCEL.id)

        new_relationship =  ParcelOwnerRelationship.objects.get(parcel_id=self.PROJECT_PARCEL.id, owner_id=new_owner.id, parcel__project=self.project1)

        self.assertEqual(new_relationship.date_ownership_ceased, datetime.date(2023, 5, 10))

        # Delete
        url_string = reverse('lms:delete_relationship', kwargs=kwargs)
        request = self.auth_post_request(url_string, data)
        response = RelationshipView.as_view()(request, **kwargs)

        self.assertTrue(response.status_code, HTTPStatus.OK)


        self.assertFalse(ParcelOwnerRelationship.objects.filter(parcel_id=self.PROJECT_PARCEL.id, owner_id=new_owner.id, parcel__project=self.project1).exists())

class InfoViewTestCase(LMSViewTestCase):
    """
    This is test case for NoteView. It is designed for other classes that is inherited from InfoView. 

    Required property:
    - view
    - model
    - name
    - create_kwargs
    """

    view: InfoView = NoteView
    model: models.Model = LandParcelOwnerNote
    name = 'note'

    create_kwargs = {
        'name': 'a',
        'content': 'a'
    }
    """Kwargs to pass in model.objects.create(**kwargs)
    
    - Automatic added property: owner, user_created, user_updated
    """
    
    def setUp(self):
        super().setUp()
        project_parcel = ProjectParcel.objects.get(id=uuid.UUID(int=1))
        self.first_relationship = ParcelOwnerRelationship.objects.create(
            parcel=project_parcel, 
            owner=self.first_owner,
            user_created=self.logged_in_user,
            user_updated=self.logged_in_user
            )
    
    def test_require_name_content(self):
        self.assertIsNotNone(self.create_kwargs.get('name'), 'name is required')
        self.assertIsNotNone(self.create_kwargs.get('content'), 'content property is required')
        
    def test_get__queryset_always_exist(self):
        """ Test if queryset exists"""
        object = self.model.objects.create(**self.create_kwargs, owner=self.first_owner, user_created=self.logged_in_user, user_updated=self.logged_in_user)
        kwargs = {'slug': self.project1.slug, 'owner': self.first_owner.id}
        url_string = reverse(f'lms:{self.name}s', kwargs=kwargs)
        print('url_string', url_string)
        view: InfoView = self.setUp_auth_view(self.view(), url_string, **kwargs)

        self.assertIsNotNone(view.queryset)
        # self.assertTrue(view.queryset.all().length, 0)

        kwargs = {'slug': self.project1.slug, 'owner': self.first_owner.id, f'{self.name}': object.id}
        url_string = reverse(f'lms:{self.name}', kwargs=kwargs)
        view = self.setUp_auth_view(self.view(), url_string, **kwargs)

        self.assertIsNotNone(view.queryset)

        # Modify
        url_string = reverse(f'lms:modify_{self.name}', kwargs=kwargs)
        view = self.setUp_post_auth_view(self.view(), url_string, {}, **kwargs)
        self.assertIsNotNone(view.queryset)

        # Delete
        url_string = reverse(f'lms:delete_{self.name}', kwargs=kwargs)
        view = self.setUp_post_auth_view(self.view(), url_string, {}, **kwargs)
        self.assertIsNotNone(view.queryset)
        

    def test_get_single__instance_exists(self):
        object = self.model.objects.create(**self.create_kwargs, owner=self.first_owner, user_created=self.logged_in_user, user_updated=self.logged_in_user)
        kwargs = {'slug': self.project1.slug, 'owner': self.first_owner.id, f'{self.name}': object.id}
        url_string = reverse(f'lms:{self.name}', kwargs=kwargs)
        view: InfoView = self.setUp_auth_view(self.view(), url_string=url_string, **kwargs)

        self.assertIsNotNone(view.instance)
        self.assertIsInstance(view.instance, self.model)
    
    def test_CRUD(self):
        """
        """
        new_owner = ParcelOwner.objects.create(first_name='Test 2', last_name='Test 2', project=self.project1, user_created=self.logged_in_user, user_updated=self.logged_in_user)

        # Create
        kwargs = {'slug': self.project1.slug, 'owner': new_owner.id}
        url_string = reverse(f'lms:{self.name}s', kwargs=kwargs)
        data = {**self.create_kwargs, 'owner': new_owner.id,  'user_created': self.logged_in_user, 'user_updated': self.logged_in_user}

        request = self.auth_post_request(url_string, data=data)
        response = self.view.as_view()(request, **kwargs)

        self.assertTrue(self.model.objects.filter(name=self.create_kwargs.get('name'), owner=new_owner).exists(), 
                        f'After {self.name} creation with name {self.create_kwargs.get("name")}, it is not created in the database.')
        self.assertEqual(response.status_code, HTTPStatus.OK, f'Unable to create {self.name} - data: {data}')
        new_info_object = self.model.objects.get(name=self.create_kwargs.get('name'), owner=new_owner)

        # Read
        kwargs = {**kwargs, f'{self.name}': new_info_object.id}
        url_string = reverse(f'lms:{self.name}', kwargs=kwargs)
        
        request = self.auth_request(url_string)
        response = self.view.as_view()(request, **kwargs)

        view = self.setUp_auth_view(self.view(), url_string, **kwargs)

        self.assertEqual(view.instance.id, new_info_object.id, f'Get {self.name} ({view.instance.id}: Return wrong {self.name}\'s id when getting single {self.name}) ')
        self.assertEqual(response.status_code, HTTPStatus.OK, f'Unable to read {self.name} ({new_info_object.id})')
        # Update
        url_string = reverse(f'lms:modify_{self.name}', kwargs=kwargs)
        
        new_data = {'name': 'aa'}
        request = self.auth_post_request(url_string, data={**data, **new_data})
        response = self.view.as_view()(request, **kwargs)

        self.assertFalse(self.model.objects.filter(name=self.create_kwargs.get('name'), owner=new_owner).exists(), 
                         f'After updating {self.name} ${new_info_object.id}, old name {self.create_kwargs.get("name")} is still exists')
        self.assertTrue(self.model.objects.filter(name='aa', owner=new_owner).exists(), 
                        f'After updating {self.name} ${new_info_object.id}, new data {new_data} is not existed')
        self.assertEqual(response.status_code, HTTPStatus.OK, f'Unable to update {self.name} ({new_info_object.id})')

        new_info_object = self.model.objects.get(name='aa', owner=new_owner)

        # Delete
        url_string = reverse(f'lms:delete_{self.name}', kwargs=kwargs)

        request = self.auth_post_request(url_string, data={})
        response = self.view.as_view()(request, **kwargs)

        self.assertFalse(self.model.objects.filter(id=new_info_object.id).exists(), f'{self.name} ({new_info_object.id}) is still existed')
        self.assertEqual(response.status_code, HTTPStatus.OK, f'Unable to delete {self.name} id {new_info_object.id}')


class CorrepondenceViewTestCase(InfoViewTestCase):
    view = CorrespondenceView
    model = LandParcelOwnerCorrespondence
    name = 'correspondence'

class ReminderViewTestCase(InfoViewTestCase):
    view = ReminderView
    model = LandParcelOwnerReminder
    name = 'reminder'

    create_kwargs = {
        'name': 'a',
        'content': 'a',
        'date_due': datetime.date.today()
    }

class TaskViewTestCase(InfoViewTestCase):
    view = TaskView
    model = LandParcelOwnerTask
    name = 'task'

    create_kwargs = {
        'name': 'a',
        'content': 'a',
        'status': 0,
        'priority': 0,
        'date_due': datetime.date.today()
    }


