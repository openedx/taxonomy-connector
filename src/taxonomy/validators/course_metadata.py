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

    @property
    def provider_class_name(self):
        """Return the name of the provider class."""
        return self.course_metadata_provider.__class__.__name__

    def validate(self):
        """
        Validate CourseMetadataProvider implements the interface as expected.

        Note: This is the only method that host platform will call,
        this method is responsible for calling the rest of the validation functions.
        """
        self.validate_get_courses()
        self.validate_get_all_courses()
        self.validate_get_course_key()
        self.validate_is_valid_course()
        self.validate_is_valid_organization()

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

    def validate_get_course_key(self):
        """
        Validate `get_course_key` attribute is a callable and has the correct signature.
        """
        get_course_key = getattr(self.course_metadata_provider, 'get_course_key')  # pylint: disable=literal-used-as-attribute
        assert callable(get_course_key)
        assert_msg = f'Invalid method signature for {self.provider_class_name}.get_course_key'
        assert str(inspect.signature(get_course_key)) == '(course_run_key)', assert_msg

    def validate_is_valid_course(self):
        """
        Validate `is_valid_course` attribute is a callable and has the correct signature.
        """
        is_valid_course = getattr(self.course_metadata_provider, 'is_valid_course')  # pylint: disable=literal-used-as-attribute
        assert callable(is_valid_course)
        assert_msg = f'Invalid method signature for {self.provider_class_name}.is_valid_course'
        assert str(inspect.signature(is_valid_course)) == '(course_key)', assert_msg

    def validate_is_valid_organization(self):
        """
        Validate `is_valid_organization` attribute is a callable and has the correct signature.
        """
        is_valid_organization = getattr(self.course_metadata_provider, 'is_valid_organization')  # pylint: disable=literal-used-as-attribute
        assert callable(is_valid_organization)
        assert_msg = f'Invalid method signature for {self.provider_class_name}.is_valid_organization'
        assert str(inspect.signature(is_valid_organization)) == '(organization_key)', assert_msg
