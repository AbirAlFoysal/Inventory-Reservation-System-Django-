from django.contrib import admin
from django.urls import path, include
from .views import HealthCheckAPI, PopulateAPI

v1_api_patterns = [
    path('', include('inventory.urls')),
]

urlpatterns = [
    path('', HealthCheckAPI.as_view()),
    # path('admin/', admin.site.urls),
    path('populate/', PopulateAPI.as_view()),
    path('api/', include([
        path('', include(v1_api_patterns)), # for v1, v2,...etc
    ])),
]
