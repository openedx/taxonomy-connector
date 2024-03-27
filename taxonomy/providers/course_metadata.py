# -*- coding: utf-8 -*-
"""
Abstract base class for course metadata providers.

All host platform must implement this provider in order for taxonomy to work.
"""
from abc import abstractmethod


class CourseMetadataProvider:
    """
    Abstract base class for course metadata providers.

    All abstract methods must be implemented for taxonomy's normal functionality.
    """

    @abstractmethod
    def get_courses(self, course_ids):
        """
        Get a list of courses matching the course ids provided in the argument.

        Arguments:
          course_ids(list<str>): A list of UUIDs in the form of a string.

        Returns:
          list<dict>: A list of courses in the form of dictionary.
            Dictionary object must have the following keys
            1. uuid: Course UUID
            2. key: Course key
            3. title: Course Title
            4. short_description: Course's short description
            5. full_description: Course's full description
        """

    @abstractmethod
    def get_all_courses(self):
        """
        Get iterator for all the courses.

        Returns:
          iterator<dict>: An iterator of courses in the form of dictionary.
            Dictionary object must have the following keys
            1. uuid: Course UUID
            2. key: Course key
            3. title: Course Title
            4. short_description: Course's short description
            5. full_description: Course's full description
        """

    @abstractmethod
    def get_course_key(self, course_run_key):
        """
        Get the course key for the given course run key.

        Arguments:
          course_run_key(str): Course run key

        Returns:
          str: course key
        """

    @abstractmethod
    def is_valid_course(self, course_key):
        """
        Validate the course key.

        Arguments:
          course_key(str): course key

        Returns:
          bool: True if course is valid, False otherwise
        """

    @abstractmethod
    def is_valid_organization(self, organization_key):
        """
        Validate the organization.

        Arguments:
          organization(str): organization key

        Returns:
          bool: True if organization is valid, False otherwise
        """
