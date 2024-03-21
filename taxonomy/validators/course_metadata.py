# -*- coding: utf-8 -*-
"""
Validator for course metadata provider.

All host platform must run this validator to make sure providers are working as expected.
"""
import inspect

from taxonomy.providers.utils import get_course_metadata_provider


class CourseMetadataProviderValidator:
    """
    Validate that the interface requirement for course metadata provider matches with the implementation.
    """

    def __init__(self, test_courses):
        """
        Setup an instance of course metadata provider.

        Since, these tests will run inside host application, list of test courses will also provided by the host.
        Args:
            test_courses (list<str>): List of course UUIDs in the form of string.
        """
        self.test_courses = test_courses
        self.course_metadata_provider = get_course_metadata_provider()

    def validate(self):
        """
        Validate CourseMetadataProvider implements the interface as expected.

        Note: This is the only method that host platform will call,
        this method is responsible for calling the rest of the validation functions.
        """
        self.validate_get_courses()
        self.validate_get_all_courses()
        self.validate_skill_validation_disabled()

    def validate_get_courses(self):
        """
        Validate `get_courses` methods has the correct interface implemented.
        """
        courses = self.course_metadata_provider.get_courses(self.test_courses)

        assert len(courses) == len(self.test_courses)

        for course in courses:
            assert 'uuid' in course
            assert 'key' in course
            assert 'title' in course
            assert 'short_description' in course
            assert 'full_description' in course

    def validate_get_all_courses(self):
        """
        Validate `get_all_courses` methods has the correct interface implemented.
        """
        courses = self.course_metadata_provider.get_all_courses()

        for course in courses:
            assert 'uuid' in course
            assert 'key' in course
            assert 'title' in course
            assert 'short_description' in course
            assert 'full_description' in course

    def validate_skill_validation_disabled(self):
        """
        Validate `skill_validation_disabled` methods has the correct interface implemented.
        """
        skill_validation_disabled_func = getattr(self.course_metadata_provider, 'skill_validation_disabled')  # pylint: disable=literal-used-as-attribute
        assert callable(skill_validation_disabled_func)
        assert str(inspect.signature(skill_validation_disabled_func)) == '(course_run_key) -> bool'
