import math
from functools import wraps
from http import HTTPStatus

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.gis.db.models import Extent, Union
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import GEOSGeometry, Polygon, MultiPolygon
from django.db import transaction
from django.db.models import Prefetch, Subquery, OuterRef, QuerySet, Count
from django.http import JsonResponse, HttpResponseNotFound, HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import resolve
from django.views import View

from datetime import datetime, timedelta

import media_file
from lms.forms import *
from native_title_management.models import *
from native_title_management.utils import utils
from project.utils.decorators import has_project_permission
from tms.models import Tenement, PermitStatusChoices
import requests


def get_choice_from_display(choices, display):
    """Returns the choice value from the display value (which is often stored in the shapefiles"""
    for value, _display in choices:
        if display == _display or value == display:
            return value

    raise ValueError(display, choices)


def convert_esri_time(time):
    """ESRI time is in MS I think?"""
    if time:
        epoch = datetime(1970, 1, 1)  # Epoch for Unix timestamps
        milliseconds = timedelta(milliseconds=time)
        return epoch + milliseconds

    return None


def re_findall_ids(string):
    """Attempts to find all NNTT id's e.g., QS2001/001"""
    import re
    return re.findall(r'\b\w+\/\d+\b', string) if string else []


DEFAULT_REST_PARAMS = {
    'where': '1=1',
    'geometryType': 'esriGeometryPolygon',
    'spatialRel': 'esriSpatialRelIntersects',
    'units': 'esriSRUnit_Meter',
    'returnGeodetic': False,
    'outFields': '*',
    'returnGeometry': True,
    'returnCentroid': False,
    'featureEncoding': 'esriDefault',
    'multipatchOption': 'xyFootprint',
    'applyVCSProjection': False,
    'returnIdsOnly': False,
    'returnUniqueIdsOnly': False,
    'returnCountOnly': False,
    'returnExtentOnly': False,
    'returnQueryGeometry': False,
    'returnDistinctValues': False,
    'cacheHint': False,
    'returnZ': False,
    'returnM': False,
    'returnExceededLimitFeatures': True,
    'sqlFormat': 'none',
    'f': 'geojson',

    'resultOffset': 0,
    'resultRecordCount': 1000,
}


def map_geojson(model, path, field_map, unique_fields=list, geometry_field='geometry', data_type="REST", extents=None, debug=False):
    """Maps GeoJSON data to a django Model.

    Parameters
    ----------
        model : Model
            The django model to be mapped to.
        path : str
            Path to the data, can be url if rest or wfs
        field_map : dict[tuple(str, func)]
           A dictionary of tuples specifying how fields will be mapped, where the key is the django model field,
           and the first item in the tuple is the GeoJSON field and the second is a function that will be run
           on the value (used in the instance the value needs to be handled differently).
        unique_fields : list[str]
            If you'd prefer the function uses update_or_create() rather than create(), the unique_fields are
            what would act as the remaining fields.
        geometry_field : str
            The name of the geometry field in the supplied model
        data_type : str
            The type of data found at the path, whether from a REST server, WFS or JSON file
        extents : str, optional
            Extents (bounding box) of the query area. This will help minimize the query parameters in the case that
            there may be millions of results.
    """
    if data_type not in ['REST', 'WFS', 'JSON']:
        raise ValueError("Invalid data_type parameter:", data_type)

    def _map_geojson(_geo_json, current_count, total_count, print_debug=False):

        if _geo_json:
            features = _geo_json.get("features", [])

            for feature in features:
                # Extract some data from the feature
                properties = feature.get("properties", {})
                geometry = feature.get("geometry", {})
                mapped_properties = {}
                unique_properties = {}

                # Map the geometry
                mapped_properties[geometry_field] = GEOSGeometry(json.dumps(geometry))

                # Map the GeoJSON properties
                for key_to, (key_from, map_func) in field_map.items():
                    value = properties.get(key_from)

                    # If there's a field function run it on the value
                    if callable(map_func):
                        value = map_func(value)

                    if key_to in unique_fields:
                        unique_properties[key_to] = value
                    else:
                        mapped_properties[key_to] = value

                # Create/update our DB entry
                if unique_fields:
                    model.objects.update_or_create(**unique_properties, defaults=mapped_properties)
                else:
                    model.objects.create(**mapped_properties)

                current_count += 1
                percent_complete = (current_count / total_count) * 100

                print(f"[{datetime.now()}][{percent_complete:.02f}%] {current_count} of {total_count}", end='\r')

        return current_count

    if data_type == 'REST':

        count_params = {'where': '1=1', 'returnCountOnly': True, 'f': 'json'}
        params = DEFAULT_REST_PARAMS.copy()

        # If a bounding box was supplied
        if extents:
            geometry_attributes = {
                'geometry': extents,
                'geometryType': 'esriGeometryEnvelope',
                'spatialRel': 'esriSpatialRelIntersects',
                'inSR': 4326,
            }
            count_params = {**count_params, **geometry_attributes}
            params = {**params, **geometry_attributes}

        # Get count information
        pjson = requests.get(path, {'f': 'pjson'}).json()
        params['resultRecordCount'] = pjson.get('maxRecordCount', 1000)
        count_request = requests.get(path + '/query', count_params)
        record_count = count_request.json().get('count', -1)

        # Start mapping the content
        print(path)
        print(f"[{datetime.now()}] Total Records: {record_count}, Records p/Query: {params['resultRecordCount']}")

        while params["resultOffset"] < record_count:

            # Perform request
            record_request = requests.get(path + '/query', params)
            geo_json = record_request.json()

            # Map the json to database models and move to next page
            params["resultOffset"] = _map_geojson(geo_json, params["resultOffset"], record_count)

        print()

    elif data_type == 'WFS':
        pass
    elif data_type == 'JSON':
        pass


def update_or_create_native_title_data(project):

    # Get the extents of the project. This isn't ideal as there could be a lot of space between them,
    # we need to figure out if we can query an arcgis server for a multipolygon (e.g., the union of all tenement areas,
    # see project.get_geometry())
    extents = project.tenements.all().aggregate(
        extent=Extent('area_polygons')
    ).get('extent')
    extents_str = '{}, {}, {}, {}'.format(*extents)

    urls = [
        # EPM
        'https://spatial-gis.information.qld.gov.au/arcgis/rest/services/Economy/MinesPermitsCurrent/MapServer/3',
        'https://spatial-gis.information.qld.gov.au/arcgis/rest/services/Economy/MinesPermitsCurrent/MapServer/2',
        # MDL
        'https://spatial-gis.information.qld.gov.au/arcgis/rest/services/Economy/MinesPermitsCurrent/MapServer/22',
        'https://spatial-gis.information.qld.gov.au/arcgis/rest/services/Economy/MinesPermitsCurrent/MapServer/25',
        # ML
        'https://spatial-gis.information.qld.gov.au/arcgis/rest/services/Economy/MinesPermitsCurrent/MapServer/40',
        'https://spatial-gis.information.qld.gov.au/arcgis/rest/services/Economy/MinesPermitsCurrent/MapServer/44',
    ]

    for url in urls:
        tenement_map = {
            'permit_state': (None, lambda x: 'QLD'),
            'permit_type': ('permittypeabbreviation', None),
            'permit_number': ('permitnumber', None),
            'permit_name': ('permitname', None),
            'permit_status': ('permitstatus', lambda x: get_choice_from_display(PermitStatusChoices.choices, x)),
            'date_lodged': ('lodgedate', convert_esri_time),
            'date_granted': ('approvedate', convert_esri_time),
            'date_commenced': ('approvedate', convert_esri_time),
            'date_expiry': ('expirydate', convert_esri_time),
            'ahr_name': ('authorisedholdername', None),
            'prescribed_minerals': ('minerals', None),
        }
        map_geojson(Tenement, url, tenement_map, unique_fields=['permit_state', 'permit_type', 'permit_number'], geometry_field='area_polygons')

    # Layer: Native Title Determinations (ID:6)
    url = "https://services2.arcgis.com/rzk7fNEt0xoEp3cX/ArcGIS/rest/services/NNTT_Custodial_AGOL/FeatureServer/6"
    field_map = {
        'tribunal_number': ('Tribunal_ID', None),
        'name': ('Name', None),
        'federal_court_number': ('FC_No', re_findall_ids),
        'federal_court_name': ('FC_Name', None),
        'date_determined': ('Determination_Date', convert_esri_time),
        'date_registered': ('NNTR_Registration_Date', convert_esri_time),
        'method': ('Determined_Method', lambda x: get_choice_from_display(METHOD_CHOICES, x)),
        'status': ('Determination_Type', lambda x: get_choice_from_display(STATUS_CHOICES, x)),
        'outcome': ('Determined_Outcome', lambda x: get_choice_from_display(OUTCOME_CHOICES, x)),
        'RNTBC_name': ('RNTBC_Name', None),
        'related_NTDA': ('Related_NTDA', re_findall_ids),
        'date_currency': ('Date_Currency', convert_esri_time),
        'NNTT_seq_no': ('NNTT_seq_no', None),
        'linked_file_no': ('Linked_File_No', None),
        'jurisdiction': ('Jurisdiction', lambda x: get_choice_from_display(AustraliaStateChoices.choices, x)),
        'claimant_type': ('Claimant_Type', lambda x: get_choice_from_display(CLAIMANT_CHOICES, x)),
        'overlap': ('Overlap', None),
    }
    map_geojson(NativeTitleDetermination, url, field_map, unique_fields=['tribunal_number'], extents=extents_str)
    # map_geojson(NativeTitleDetermination, url, field_map, unique_fields=['tribunal_number'])

    # Layer: Schedule of Native Title Determination Applications (ID:8)
    url = "https://services2.arcgis.com/rzk7fNEt0xoEp3cX/ArcGIS/rest/services/NNTT_Custodial_AGOL/FeatureServer/8"
    field_map = {
        'federal_court_number': ('FC_No', None),
        'tribunal_number': ('Tribunal_ID', None),
        'name': ('Name', None),
        'date_lodged': ('Date_Lodged', convert_esri_time),
        'date_status_effective': ('Date_Lodged', convert_esri_time),
        'status': ('Status', lambda x: get_choice_from_display(APPLICATION_STATUS_CHOICES, x)),
        'sub_status': ('RT_Status', lambda x: get_choice_from_display(REG_TEST_STATUS_CHOICES, x)),
        'date_registered': ('Date_RT_Decision', convert_esri_time),
        'representative': ('Representative', None),
        'jurisdiction': ('Jurisdiction', lambda x: get_choice_from_display(AustraliaStateChoices.choices, x)),
        'overlap': ('Overlap', None),
    }
    map_geojson(NativeTitleClaimApplication, url, field_map, unique_fields=['tribunal_number'], extents=extents_str)
    # map_geojson(NativeTitleClaimApplication, url, field_map, unique_fields=['tribunal_number'])

    # Layer: Parcel positional accuracy (ID: 3)
    url = "https://spatial-gis.information.qld.gov.au/arcgis/rest/services/PlanningCadastre/LandParcelPropertyFramework/MapServer/3"

    # Layer: Cadastral Parcels - All (ID: 4)
    # url = "https://spatial-gis.information.qld.gov.au/arcgis/rest/services/PlanningCadastre/LandParcelPropertyFramework/MapServer/4"

    # Layer: Base Parcels Only (ID: 8)
    # url = "https://spatial-gis.information.qld.gov.au/arcgis/rest/services/PlanningCadastre/LandParcelPropertyFramework/MapServer/8"
    field_map = {
        'lot': ('lot', None),
        'plan': ('plan', None),
        'tenure': ('tenure', None),
        'segment_parcel': ('segpar', None),
        'shire_name': ('shire_name', None),
        'feature_name': ('feat_name', None),
        'alias_name': ('alias_name', None),
        'locality': ('locality', None),
        'parcel_type': ('parcel_typ', None),
        'accuracy_code': ('acc_code ', None),
        'cover_type': ('cover_typ', None),
        'smis_map': ('smis_map', None),
    }
    map_geojson(Parcel, url, field_map, unique_fields=['lot', 'plan', 'segment_parcel'], extents=extents_str)
    # map_geojson(Parcel, url, field_map, unique_fields=['lot', 'plan', 'segment_parcel'])


@has_project_permission()
def nms_project(request, project, slug, *args, **kwargs):

    update_or_create_native_title_data(project)
    # update_or_create_native_title_data()
    context = {
        # 'feature_json': fea_json,
        'project': project,
        'lot_plans': Parcel.objects.filter_project_area(project),
        'native_title_determinations': NativeTitleDetermination.objects.filter_project_area(project),
        'native_title_applications': NativeTitleClaimApplication.objects.filter_project_area(project),
    }
    return render(request, 'native_title_management/base.html', context)