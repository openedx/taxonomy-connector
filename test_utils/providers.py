# -*- coding: utf-8 -*-
"""
An implementation of providers to be used in tests.
"""

from taxonomy.providers import CourseMetadataProvider
from test_utils.mocks import MockCourse


class DiscoveryCourseMetadataProvider(CourseMetadataProvider):
    """
    Discovery course metadata provider to be used in the tests.
    """

    def __init__(self, mock_courses=None):
        """
        Initialize with mocked courses.
        """
        super(DiscoveryCourseMetadataProvider, self).__init__()
        self.mock_courses = mock_courses

    def get_courses(self, course_ids):
        if self.mock_courses is not None:
            courses = self.mock_courses
        else:
            courses = [MockCourse(uuid=course_id) for course_id in course_ids]

        return [{
            'uuid': course.uuid,
            'key': course.key,
            'title': course.title,
            'short_description': course.short_description,
            'full_description': course.full_description,
        } for course in courses]
