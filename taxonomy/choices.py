"""
Module for storing django choice fields for taxonomy models.
"""
from django.db import models


class UserGoal(models.TextChoices):
    """
    User goal choices, this will be used in skills quiz.
    """

    CHANGE_CAREERS = 'change_careers', 'I want to change careers'
    GET_PROMOTED = 'get_promoted', 'I want to get promoted'
    IMPROVE_CURRENT_ROLE = 'improve_current_role', 'I want to improve at my current role'
    OTHER = 'other', 'Other'

    # Backward compatibility aliases for existing code
    ChangeCareers = CHANGE_CAREERS
    GetPromoted = GET_PROMOTED
    ImproveCurrentRole = IMPROVE_CURRENT_ROLE
    Other = OTHER


class ProductTypes(models.TextChoices):
    """
    Product types to be used in retrieving skills.
    """

    COURSE = 'course', 'Course'
    PROGRAM = 'program', 'Program'
    XBLOCK = 'xblock', 'XBlock'
    XBLOCK_DATA = 'xblock_data', 'XBlockData'

    # Backward compatibility aliases for existing code
    Course = COURSE
    Program = PROGRAM
    XBlock = XBLOCK
    XBlockData = XBLOCK_DATA
