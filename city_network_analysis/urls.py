"""
URL configuration for city_network_analysis project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from streets import views
from django.urls import path, include
from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register(r'metric-values', views.MetricValueViewSet)
router.register(r'metrics', views.MetricViewSet)
router.register(r'cities', views.CityViewSet)
router.register(r'nodes', views.NodeViewSet)
router.register(r'edges', views.EdgeViewSet)

urlpatterns = [
    path("admin/", admin.site.urls),
    path('db_map/', views.db_map_view, name='db_map'),
    # path('api/db_map/', views.get_data, name='network_data'),
    path('city-metrics/', views.city_metrics_page, name='city_metrics_page'),
    path('api/', include(router.urls)),
    path('geojson/edges/', views.EdgeGeoJSONView.as_view(), name='geojson-edges'),
    path('geojson/nodes/', views.NodeGeoJSONView.as_view(), name='geojson-nodes'),
]
