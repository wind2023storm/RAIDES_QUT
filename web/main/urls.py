"""
URL configuration for main project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/dev/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from django.conf.urls.static import static

from main import settings

if settings.DEBUG:
    from main.debug import views

urlpatterns = [
    # Django admin page
    path('admin/', admin.site.urls),

    # Main landing page
    path('', include('website.urls')),

    # App urls
    path('dashboard/', include('appboard.urls'), name='appboard'),
    path('geochem/', include('geochem.urls'), name='geochem'),
    path('project/', include('project.urls'), name='project'),
    path('lms/', include('lms.urls'), name='lms'),
    path('nms/', include('native_title_management.urls'), name='nms'),
    path('tms/', include('tms.urls'), name='tms'),
    path('user/', include('user.urls'), name='user'),
    path('interactive_map/', include('interactive_map.urls'), name='interactive_map'),
    path('gis/', include('geodesk_gis.urls'), name='gis'),
    # path('search_engine/', include('search_engine.urls'), name='search_engine'),
    path('project_management/', include('project_management.urls'), name='project_management'),
    path('forms/', include('autoform.urls'), name='autoform'),
    path('media_file/', include('media_file.urls'), name='media_file'),

    path('notification/', include('notification.urls'), name='notification'),
]

if settings.DEBUG:
    urlpatterns += [
        path('debug/', views.platform_debug_setup_view, name='debug_setup'),
        # path('testapi/', include('testapi.urls'), name='testapi')
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)