# -*- coding: utf-8 -*-
"""
Taxonomy Connector URL Configuration.
"""

from django.urls import re_path

from taxonomy import views

urlpatterns = [
    re_path(
        r"^admin/taxonomy/refresh_course_skills/$", views.RefreshCourseSkills.as_view(), name="refresh_course_skills"
    ),
]
