from ast import Not
import json
from typing import List
from django.urls import reverse
from regex import R

from lms.models import ProjectParcel, Parcel
from lms.managers import ParcelProjectManager
from project.models import Project

def get_feature_from(project_parcel: ProjectParcel, **extra_properties):
  """
    Get GeoJSON Feature in Format:

    ```
    "type": "Feature",
    "geometry": json.loads(parcel.geometry.geojson),
    "properties": {
        "id": parcel.id,
        "name": parcel.feature_name,
        "lot": parcel.lot,
        "plan": parcel.plan,
        "tenure": parcel.tenure,
        "url": project_parcel_url
    }
    ```
  """
  parcel = project_parcel.parcel

  project_parcel_url = reverse('lms:parcel', kwargs={'slug': project_parcel.project.slug, 'parcel': project_parcel.id})

  feature = { 
      "type": "Feature",
      "geometry": json.loads(parcel.geometry.geojson),
      "properties": {
          "id": parcel.id,
          "name": parcel.feature_name,
          "lot": parcel.lot,
          "plan": parcel.plan,
          "tenure": parcel.tenure,
          "url": project_parcel_url,
          **extra_properties
      }
  }

  return feature

def get_feature_collection_from_project_parcels(project_parcels: ParcelProjectManager):
  """
    ### Description
    Return feature collection rendered by frontend

    ```
    feature_collection = {
      "type": "FeatureCollection",
      "features": features,
      "project_geometry": json.loads(parcel_project_geometry.geojson)
    }
    ```

    ### To render to frontend in Django context:

    ```
    const features = convert_project_parcels_to_feature_collection(project_parcels)
    ...
    context = {
      "feature_collection": json.dumps(features, default=str)
    }
    ```
  """
  features = []
  project_slug = ''

  if len(project_parcels) == 0:
    return {}

  for project_parcel in project_parcels:
    project_slug = project_parcel.project.slug

    feature = get_feature_from(project_parcel=project_parcel)
    
    if (hasattr(project_parcel, "owners_count")):
      feature["properties"]["owners_count"] = project_parcel.owners_count

    features.append(feature)

  parcel_project_geometry = Project.objects.get(slug=project_slug ).get_geometry()
    
  feature_collection = {
    "type": "FeatureCollection",
    "features": features,
  }

  if parcel_project_geometry is not None:
    feature_collection["project_geometry"] = json.loads(parcel_project_geometry.geojson)

  return feature_collection


    