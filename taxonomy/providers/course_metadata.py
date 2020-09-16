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
            1. key: Course key
            1. title: Course Title
            1. short_description: Course's short description
            2. full_description: Course's full description
        """
