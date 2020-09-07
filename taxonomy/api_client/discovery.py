"""
Utilities to communicate with the discovery service.

All the communication with discovery should go through this gateway.
"""
from django.db.models import Q

try:
    from course_discovery.apps.course_metadata.models import Course
except ImportError:
    Course = None


def get_courses(options):
    """
    Retrieve the courses from discovery.
    """
    return Course.everything.filter(
        Q(uuid__in=options['course'])
    ).distinct()


def extract_course_description(course):
    """
    Extract the course description from course object.
    """
    return course.full_description if course else None
