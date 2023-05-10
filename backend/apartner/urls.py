"""Apartner URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
import debug_toolbar
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_nested import routers

admin.site.site_header = 'Apartner Admin'
admin.site.index_title = 'Admin'
router = routers.DefaultRouter()

urlpatterns = [
    path('admin/', admin.site.urls),

    #todo:
    # path('', views.getRoutes, name="routes"),
    path('', include('main_page.urls')),
    path('core/', include(('core.urls', 'core'), namespace='core'),name = 'core'),
    path('owner/', include(('owner.urls', 'owner'), namespace='owner'),name = 'owner'),
    path('searcher/', include(('searcher.urls', 'searcher'), namespace='searcher'),name = 'searcher'),
    path('renter/', include(('renter.urls', 'renter'), namespace='renter'),name = 'renter'),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    path('__debug__/', include(debug_toolbar.urls)),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_create'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
