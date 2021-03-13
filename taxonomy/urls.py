# -*- coding: utf-8 -*-
"""
Taxonomy Connector URL Configuration.
"""

from django.urls import re_path, include

from taxonomy import views
from taxonomy.api.v1.urls import urlpatterns as api_v1_urlpatterns


urlpatterns = [
    re_path(
        r"^admin/taxonomy/refresh_course_skills/$", views.RefreshCourseSkills.as_view(), name="refresh_course_skills"
    ),
]

urlpatterns += api_v1_urlpatterns
