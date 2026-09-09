"""
Taxonomy v1 API URLs.
"""
from django.urls import include, path

urlpatterns = [
    path('api/', include('taxonomy.api.urls')),
]
