import os
import json
from http import HTTPStatus

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.shortcuts import render

from project.models import Project
from project.utils.decorators import has_project_permission
from tms.models import Tenement

from django.contrib.gis.geos import GEOSGeometry, MultiPolygon
from lms.models import LandParcel
from datetime import datetime, date

JSON_DIRECTORY = 'interactive_map/static/interactive_map/json/'

def load_json(file_path):
    """
    Load a JSON file from the specified file path and return its contents as a dictionary.

    Args:
        file_path (str): The path to the JSON file to load.

    Returns:
        dict: The contents of the JSON file as a dictionary.
    """
    try:
        with open(file_path) as file:
            return json.load(file)
    except Exception as e:
        raise ValueError(f"Error loading JSON file: {e}")

def get_tenements_data():
    """
    Returns a dictionary containing the tenements data from the JSON file.

    :return: A dictionary containing the tenements data.
    """
    return load_json(os.path.join(JSON_DIRECTORY, 'tenements.json'))

def process_cadastre_json(file_path):
    """Inserts cadastre data from a JSON file into the LandParcel model in the database.

    Args:
        file_path (str): The path to the JSON file containing the cadastre data.
    """

    cadastre_data = load_json(file_path)
    
    # Insert data into the database
    for feature in cadastre_data['features']:
        geometry_json = feature['geometry']
        geometry = GEOSGeometry(json.dumps(geometry_json))
        
        # Convert Polygon geometry to MultiPolygon if needed
        if geometry.geom_type == 'Polygon':
            geometry = MultiPolygon(geometry)

        LandParcel.objects.update_or_create(
            lot=feature['properties'].get('LOT'),
            plan=feature['properties'].get('PLAN'),
            geometry=geometry
        )

    print("Cadastre data inserted into the database.")

def is_date_expired(string_date: str, date_format: str = "%Y-%m-%d"):
    """
    Check if a given date string is expired.

    Args:
        string_date (str): The date string to check.
        date_format (str): The format of the date string. Defaults to "%Y-%m-%d".

    Returns:
        bool: True if the date is expired, False otherwise.
    """
    converted_date = datetime.strptime(string_date, date_format).date()
    current_date = date.today()
    return converted_date < current_date
        
def get_status(properties):
    """
    Returns the status of a permit based on its properties.
    
    Args:
        properties (dict): A dictionary containing the properties of the permit.
        
    Returns:
        str: The status of the permit, which can be 'A' (Application), 'N' (Not Renewed), or 'G' (Granted).
    """
    if properties['PERMITST_1'] == "Application":
        return 'A'
    
    if properties['PERMITST_1'] == "Granted" and is_date_expired(properties['EXPIRYDATE']) and properties['PERMITST_2'] != "Renewal Lodged":
        return 'N'
    
    return 'G'

def process_tenement_json():
    """
    Processes a JSON file containing tenement data and inserts/updates the data in the database.

    Args:
        file_path (str): The path to the JSON file.

    Raises:
        ValueError: If the JSON file is invalid.

    Returns:
        None
    """
    
    tenement_data = get_tenements_data()


    # Insert data into the database
    for feature in tenement_data['features']:
        properties = feature['properties']
        geometry_json = feature['geometry']
        geometry = GEOSGeometry(json.dumps(geometry_json))
        
        # Convert Polygon geometry to MultiPolygon if needed
        if geometry.geom_type == 'Polygon':
            geometry = MultiPolygon(geometry)

        Tenement.objects.update_or_create(
            permit_state='QLD',
            permit_type=properties['PERMITTY_2'],
            permit_number=properties['PERMITNUMB'],
            defaults={
                'permit_name': properties['PERMITNAME'],
                'permit_status': get_status(properties),
                'date_lodged': properties['LODGEDATE'],
                'date_granted': properties['APPROVEDAT'],
                'date_expiry': properties['EXPIRYDATE'],
                'ahr_name': properties['AUTHORIS_1'],
                'area_polygons': geometry,
                'native_title_description': properties['NATIVETITL']
            }
        )

"""uncomment below if you want to update tenement and cadastre data"""
#process_tenement_json()
#process_cadastre_json(os.path.join(JSON_DIRECTORY, 'cadastre.json'))

# connect to the interactive map
def interactive_map(request):
    return render(request, 'interactive_map/interactive_map.html', {})


# connects to the json files that display the layers
def get_tenements_json(request, project=None, slug=None, permit_state = None, permit_type=None, permit_number=None, tenement=None, state=None):
    json_data = load_json(os.path.join(JSON_DIRECTORY, 'tenements.json'))
    return JsonResponse(json_data)

# connects to the json files that display the layers
def get_multi_tenements_json(request, project=None, slug=None, permit_state = None, permit_type=None, permit_number=None, tenement=None, state=None):
    json_data = {'EPCA': load_json(os.path.join(JSON_DIRECTORY, 'epc_applications.json')),
         'EPCG': load_json(os.path.join(JSON_DIRECTORY, 'epc_granted.json')),
         'EPMA': load_json(os.path.join(JSON_DIRECTORY, 'epm_applications.json')),
         'EPMG': load_json(os.path.join(JSON_DIRECTORY, 'epm_granted.json')),
         'MDLA': load_json(os.path.join(JSON_DIRECTORY, 'mdl_applications.json')),
         'MDLG': load_json(os.path.join(JSON_DIRECTORY, 'mdl_granted.json')),
         'MLA': load_json(os.path.join(JSON_DIRECTORY, 'ml_applications.json')),
         'MLG': load_json(os.path.join(JSON_DIRECTORY, 'ml_granted.json')),
        }
    return JsonResponse(json_data)

# Cadastre
def get_cadastre(request):
    json_data = load_json(os.path.join(JSON_DIRECTORY, 'cadastre.json'))
    return JsonResponse(json_data)

@has_project_permission()
def get_project_map(request, project: Project, slug):
    """Retrieves the Tenements in JSON format from a Project's Dashboard. """
    tenements = project.tenements.all()
    targets = project.targets.all()
    # get the permit type and number to be displayed on project map
    context = [{
        "permit_type": tenement.permit_type,
        "permit_number": tenement.permit_number,
        "permit_status": tenement.permit_status
    } for tenement in tenements]

    coordinates = [{
        'name': target.name,
        'description': target.description,
        'location': target.location,  # target.location,
    } for target in targets]
    # Send it off
    return render(request, "interactive_map/project_map.html",
                  {'context': json.dumps(context, default=str),
                   'targets': json.dumps(coordinates, default=str),
                   }, content_type='application/json')


@login_required
def get_tenement_map(request, permit_state, permit_type, permit_number):
    """Returns the tenement in JSON format that the requesting user is a member of
        along with the html of the tenement map.
    """

    try:
        tenement = Tenement.objects.get(permit_state=permit_state, permit_type=permit_type, permit_number=permit_number)
    except ObjectDoesNotExist:
        pass  # 404 error something

    try:
        project = Project.objects.prefetch_related('targets').get(tenements__id=tenement.id, members__user=request.user)
        targets = project.targets.all()

        coordinates = [{
            'name': target.name,
            'description': target.description,
            'location': target.location,  # target.location,
            'actions': None,
        } for target in targets]
    except Exception:
        coordinates = []

    context = {
        'tenement_permit': json.dumps([{'tenement_permit': tenement.permit_id}], default=str),
        'targets': json.dumps(coordinates, default=str),
    }

    # Send it off
    return render(request, "interactive_map/tenement_map.html", context, content_type='application/json')
