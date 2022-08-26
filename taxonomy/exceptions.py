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


class ProgramMetadataNotFoundError(Exception):
    """
    Exception to raise when program metadata is not found for program.
    """


class InvalidCommandOptionsError(Exception):
    """
    Exception to raise when incorrect command options are provided.
    """
