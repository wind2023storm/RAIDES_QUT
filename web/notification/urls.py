from django.urls import path, re_path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'notification'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('room/<str:room_id>/', views.RoomView.as_view(), name='room'),
]

if settings.DEBUG:
    urlpatterns += [
        path('toggle/', views.ToggleView.as_view(), name='cycle_user')
    ]
