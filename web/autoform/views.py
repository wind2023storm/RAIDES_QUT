import json

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.db.models import Prefetch, Q
from django.shortcuts import render

from datetime import datetime

from autoform.forms import ApplicationForExplorationPermit
from tms.models import Tenement, TenementHolder

UserModel = get_user_model()


@login_required
def application_for_epm(request):
    # tenements = Tenement.objects.filter(permit_type="EPM", permit_number=28119).prefetch_related(
    #     Prefetch('holders'),
    #     Prefetch('holders', queryset=TenementHolder.objects.filter(is_authorised_holder=True),
    #              to_attr='authorised_holder')
    # )
    #
    # tenement_dict = [{
    #     'permit_id': tenement.permit_id,
    #     'permit_type': tenement.permit_type,
    #     'permit_number': tenement.permit_number,
    #     'permit_state': tenement.get_permit_state_display(),
    #     'ahr_name': tenement.ahr_name if tenement.ahr_name else '',
    #     'ahr_email': tenement.ahr_email if tenement.ahr_email else '',
    #     'ahr_phone_number': tenement.ahr_phone_number if tenement.ahr_phone_number else '',
    #     'authorised_holder': {
    #         'name': tenement.authorised_holder[0].name_main,
    #         'address': tenement.authorised_holder[0].address,
    #     },
    #     'holders': [{
    #         'name': holder.name_main,
    #     } for holder in tenement.holders.all()],
    #     # 'environmental_authority': vars(tenement.environmental_authority[0])
    #
    # } for tenement in tenements]

    # This is an example context dictionary for usage of the autoform.
    # `page_title` and `templates` are required fields, and `field_data` is optional.
    # this context must be passed to the 'autoform/autoform.html' template.
    context = {
        # The title shown on the browser header and tab
        'page_title': 'QLD Exploration Permit Application Forms',

        # Place paths to templates you want to load on the page here
        # the order in this list defines the order they're stacked on the front-end
        'templates': [
            # 'autoform/forms/entry_notice_for_private_land.html',
            'autoform/forms/AHR_form.html',
            'autoform/forms/statement_of_financial_capabilities.html',
            'autoform/forms/statement_of_financial_commitments.html',
        ],

        # field_data is used to populate auto-fields when the template is first rendered
        # keep in mind that this information is stored in the client browser, so be mindful
        # of what you pass through here.
        'field_data': {
            'current_date': datetime.today().date().strftime('%d/%m/%Y'),
            'company': {
                'name': request.user.company,
                'director': {
                    'name': request.user.full_name,
                }
            },
            # 'tenement': tenement_dict[0]
        }
    }

    return render(request, 'autoform/autoform.html', context)
