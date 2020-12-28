# -*- coding: utf-8 -*-
"""
Exceptions that will be used by the taxonomy connector to indicate different errors.
"""


class TaxonomyAPIError(Exception):
    """
    Exception to raise when something goes wrong while talking to the EMSI service.
    """


class CourseMetadataNotFoundError(Exception):
    """
    Exception to raise when course metadata was not found for course.
    """


class CourseSkillsRefreshError(Exception):
    """
    Exception to raise when errors were encountered during refreshing the course skills.
    """
