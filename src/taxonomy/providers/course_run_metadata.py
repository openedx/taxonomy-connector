# -*- coding: utf-8 -*-
"""
Abstract base class for course run metadata providers.

All host platform must implement this provider in order for taxonomy to work.
"""
from abc import abstractmethod
from typing import NamedTuple


class CourseRunContent(NamedTuple):
    """
    NamedTuple to store xblock content.
    """
    # Course run key
    course_run_key: str
    # Course key
    course_key: str


class CourseRunMetadataProvider:
    """
    Abstract base class for course run metadata providers.

    All abstract methods must be implemented for taxonomy's normal functionality.
    """

    @abstractmethod
    def get_course_runs(self, course_run_keys):
        """
        Get a list of course runs matching the course keys provided in the argument.

        Arguments:
          course_run_keys(list<str>): A list of course_run_keys in the form of a string..

        Returns:
          list<CourseRunContent>: A list of CourseRunContent objects.
        """

    @abstractmethod
    def get_all_published_course_runs(self):
        """
        Get iterator for all published course runs.

        Returns:
          iterator<CourseRunContent>: A iterator of CourseRunContent objects.
        """
