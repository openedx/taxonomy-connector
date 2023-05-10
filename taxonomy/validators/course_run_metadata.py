# -*- coding: utf-8 -*-
"""
Validator for course run metadata provider.

All host platform must run this validator to make sure providers are working as expected.
"""
from taxonomy.providers.course_run_metadata import CourseRunContent
from taxonomy.providers.utils import get_course_run_metadata_provider


class CourseRunMetadataProviderValidator:
    """
    Validate that the interface requirement for course run metadata provider matches with the implementation.
    """

    def __init__(self, test_courses):
        """
        Setup an instance of course run metadata provider.

        Since, these tests will run inside host application, list of test courses will also provided by the host.
        Args:
            test_courses (list<str>): List of course run keys in the form of string.
        """
        self.test_courses = test_courses
        self.course_run_metadata_provider = get_course_run_metadata_provider()

    def validate(self):
        """
        Validate CourseMetadataProvider implements the interface as expected.

        Note: This is the only method that host platform will call,
        this method is responsible for calling the rest of the validation functions.
        """
        self.validate_get_course_runs()
        self.validate_get_all_published_course_runs()

    def validate_get_course_runs(self):
        """
        Validate `get_course_runs` methods has the correct interface implemented.
        """
        courses = self.course_run_metadata_provider.get_course_runs(self.test_courses)

        assert len(courses) == len(self.test_courses)

        for course in courses:
            assert isinstance(course, CourseRunContent)

    def validate_get_all_published_course_runs(self):
        """
        Validate `get_all_courses` methods has the correct interface implemented.
        """
        courses = self.course_run_metadata_provider.get_all_published_course_runs()

        for course in courses:
            assert isinstance(course, CourseRunContent)
