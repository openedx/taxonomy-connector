"""
Tests for the `taxonomy` url module.
"""
from unittest import TestCase

from django.urls import resolve

from taxonomy.views import RefreshCourseSkills


class TestUrls(TestCase):
    """
    Functional url Tests for RefreshCourseSkills.
    """

    def test_home_url_resolves_home_view(self):
        view = resolve('/admin/taxonomy/refresh_course_skills/')
        self.assertEqual(view.func.view_class, RefreshCourseSkills)
