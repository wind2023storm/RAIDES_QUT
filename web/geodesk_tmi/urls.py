from . import views
from django.urls import path, include

app_name = 'tmi'


urlpatterns = [
    path("compare/", views.compare, name="compare"),
    path("project_area_input_selection/", views.project_area_input_selection, name="project_area_input_selection"),
    path("output_model_result", views.output_model_result, name="output_model_result"),
    path("extract_image", views.extract_image, name="extract_image"),
    path("display_image_update", views.display_image_update, name="display_image_update"),
    path("store_results", views.store_results, name="store_results"),
    path('retrieve_results', views.retrieve_results, name='retrieve_results'),
    path('clear_results', views.clear_results, name='clear_results'),
    path('forward_history', views.forward_history, name="forward_history"),
    path('back_history', views.back_history, name="back_history")
 ]
