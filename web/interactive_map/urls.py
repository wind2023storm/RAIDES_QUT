from django.urls import path
from . import views

app_name = "interactive_map"

urlpatterns = [
    # interactive map
    path('', views.interactive_map, name = 'home'),
    
    # Polygon Data
    path('get/tenements/', views.get_tenements_json, name = 'get_tenements_json'),
    path('cadastre/', views.get_cadastre, name = 'cadastre'),
]