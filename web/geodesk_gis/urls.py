from . import views
from django.urls import path

app_name = 'gis'


urlpatterns = [
    path('plotter', views.plotter, name="plotter"),
    path('tmi', views.tmi, name="tmi"),
    path('upload', views.file_uploader, name="file_uploader"),
    path('map', views.mapplotter, name="mapplotter"),
    path('serve', views.serve_tif, name="serve"),
    path('crop', views.crop_image, name="crop")
]
 