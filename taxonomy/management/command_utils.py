"""
Useful utilities for management commands.
"""

from django.core.management.base import CommandError


def get_mutually_exclusive_required_option(options, *selections):
    """
    Validates that exactly one of the 2 given options is specified.
    Returns the name of the found option.
    """

    selected = [sel for sel in selections if options.get(sel)]
    if len(selected) != 1:
        selection_string = u', '.join('--{}'.format(selection) for selection in selections)

        raise CommandError(u'Must specify exactly one of {}'.format(selection_string))
    return selected[0]


def fetch_course_description(course_key):
    """
    Fetches the course description.
    """
    #TODO
    return "Welcome to this course on drainage for controlling water and salt levels in agricultural lands. In this course, you will advance your knowledge of drainage systems and solutions to help to secure a sustainable food supply to feed the growing world population. We have prepared five interesting modules and if you're keen to start, head directly to Module 1 to meet your teachers and fellow students."
