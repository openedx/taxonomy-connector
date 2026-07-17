"""
Taxonomy v1 API URLs.
"""
from django.urls import include, path

urlpatterns = [
    path('v1/', include('taxonomy.api.v1.urls')),
]
