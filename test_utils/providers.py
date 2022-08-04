# -*- coding: utf-8 -*-
"""
An implementation of providers to be used in tests.
"""

from taxonomy.providers import CourseMetadataProvider, ProgramMetadataProvider
from test_utils.mocks import MockCourse, MockProgram


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

    def get_all_courses(self):
        """
        Get iterator of all the courses
        """
        if self.mock_courses is not None:
            courses = self.mock_courses
        else:
            courses = [MockCourse() for _ in range(5)]
        for course in courses:
            yield {
                'uuid': course.uuid,
                'key': course.key,
                'title': course.title,
                'short_description': course.short_description,
                'full_description': course.full_description,
            }


class DiscoveryProgramMetadataProvider(ProgramMetadataProvider):
    """
    Discovery program metadata provider to be used in the tests.
    """

    def __init__(self, mock_programs=None):
        """
        Initialize with mocked courses.
        """
        super(DiscoveryProgramMetadataProvider, self).__init__()
        self.mock_programs = mock_programs

    def get_programs(self, program_ids):
        if self.mock_programs is not None:
            programs = self.mock_programs
        else:
            programs = [MockCourse(uuid=program_id) for program_id in program_ids]

        return [{
            'uuid': program.uuid,
            'title': program.title,
            'subtitle': program.subtitle,
            'overview': program.overview,
        } for program in programs]

    def get_all_programs(self):
        """
        Get iterator of all the courses
        """
        if self.mock_programs is not None:
            programs = self.mock_programs
        else:
            programs = [MockProgram() for _ in range(5)]
        for program in programs:
            yield {
                'uuid': program.uuid,
                'title': program.title,
                'subtitle': program.subtitle,
                'overview': program.overview,
            }
