from datetime import datetime

from dateutil.relativedelta import relativedelta
from django.core.handlers.wsgi import WSGIRequest
from django.db import models
from django.db.models import Prefetch

from main.utils import django_date


class TaskManager(models.Manager):

    def generate_complaince_documents(self, tenement):
        """One of the requirements is that tenements should be auto populated with certain compliance tasks. It's
        not known if there are any files that should be attached to these. They are only added if a tenement has a
        commencement date."""
        anniversary: datetime = tenement.date_anniversary

        def anniversary_add(**kwargs):
            return anniversary + relativedelta(**kwargs)

        def anniversary_sub(**kwargs):
            return anniversary - relativedelta(**kwargs)

        # If the stored commencement date isn't a datetime object this won't work. Scraper automatically converts input
        # TODO: Ensure the FTP adheres to this requirement
        if isinstance(tenement.date_commenced, datetime):

            # Use django local timezone to calculate next dates
            next_quarter = django_date.next_quarter()
            next_month = django_date.next_month()

            tasks = []
            if tenement.permit_type in ['EPM', 'EPC', 'MDL', 'ML']:
                tasks += [
                    self.create(name='Annual Rent', description='Payment', due_date=anniversary),
                    self.create(name='Annual EA Fee', description='Payment', due_date=anniversary),
                    self.create(name='Annual Activities Report', description='Payment', due_date=anniversary),
                    self.create(name='Annual EA Return', description='Report/Form', due_date=anniversary_add(days=30)),
                    self.create(name='Renewal Application', description='Report/Form',
                                 due_date=anniversary_sub(days=60)),
                    self.create(name='ABS Return', description='Report & Supporting Docs',
                                 due_date=anniversary_sub(months=6 if self.tenement.permit_type == 'ML' else 2)),
                ]

            if tenement.permit_type in ['EPM', 'EPC', 'MDL']:
                tasks += [
                    self.create(name='Annual Expenditure Report', description='Report',
                                 due_date=anniversary_add(days=30)),
                ]

            if tenement.permit_type in ['EPM', 'EPC']:
                tasks += [
                    self.create(name='Expenditure Variation', description='Electronic Lodgement',
                                 due_date=anniversary),
                ]

            if tenement.permit_type in ['MDL', 'ML']:
                tasks += [
                    self.create(name='Council Rates', description='Online Form', due_date=next_quarter),
                ]

            if tenement.permit_type == 'ML':
                tasks += [
                    self.create(name='Safety Census', description='Government Doc', due_date=next_quarter),
                    self.create(name='Royalty Return Document', description='Payment', due_date=next_month),
                    self.create(name='Royalty Payment', description='Documents', due_date=next_quarter),
                    self.create(name='Production and Sales Return', description='GSQ Portal Lodgement',
                                 due_date=next_month),
                ]

            for task in tasks:
                task.authority = tenement.project.owner
                task.tenement = tenement
                task.save()


class TenementManager(models.Manager):

    def filter_permission(self, request: WSGIRequest, permission: int, **kwargs):
        return self.filter(**kwargs).select_related('project').prefetch_related(
            Prefetch('project__members',
                     queryset=request.user.memberships.filter(permission__gte=permission).select_related('user'),
                     to_attr='request_member')
        )

    def to_datatable(self, request, **kwargs):
        """Performs a query for Tenement objects based on kwargs and returns the data formatted for JS datatables.
        Kwargs are supplied as normal query arguments.

        Only tenements where the requesting user exists as a member will be returned.

        tenements = Tenement.objects.to_datatable(request, project=my_project)
        """
        tenements = self.filter(**kwargs).select_related('project').prefetch_related(
            Prefetch('project__members',
                     queryset=request.user.memberships.all().select_related('user'),
                     to_attr='request_member')
        ).all()

        # TODO: Handle for tenements not in projects if required. Simply just a couple if statements in the loop
        #   to filter out any project/member related information
        return {
            'data': [{
                'state': tenement.permit_state,
                'permit': {
                    'type': tenement.permit_type,
                    'number': tenement.permit_number,
                    'display': tenement.permit_id,
                    'slug': tenement.get_absolute_url()
                },
                'project': {
                    'name': tenement.project.name,
                    'slug': tenement.project.get_absolute_url()
                },
                'status': tenement.get_permit_status_display(),
                'date_granted': tenement.date_granted,
                'tags': None,  # TODO: Is this something that's actually used?
                'permission': tenement.project.request_member[0].get_permission_display(),
                'actions': tenement.project.request_member[0].permission,

            } for tenement in tenements if tenement.project.request_member or request.user.is_superuser]
        }
