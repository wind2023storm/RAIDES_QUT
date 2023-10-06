from . import views
from django.urls import path, include

app_name = 'gis'


urlpatterns = [
    path('plotter', views.plotter, name="plotter"),
    path('tmi', views.tmi, name="tmi"),
    path('upload', views.file_uploader, name="file_uploader"),
    path('map', views.mapplotter, name="mapplotter"),
    path('serve', views.serve_tif, name="serve"),
    path('crop', views.crop_image, name="crop"),
    path("compare/", views.compare, name="compare"),
    path("project_area_input_selection/", views.project_area_input_selection, name="project_area_input_selection"),
    path("output_model_result", views.output_model_result, name="output_model_result"),
    path("extract_image", views.extract_image, name="extract_image"),
    path("display_image_update", views.display_image_update, name="display_image_update")
 ]
