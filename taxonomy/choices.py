"""
Module for storing django choice fields for taxonomy models.
"""
from djchoices import ChoiceItem, DjangoChoices


class UserGoal(DjangoChoices):
    """
    User goal choices, this will be used in skills quiz.
    """

    ChangeCareers = ChoiceItem('change_careers', 'I want to change careers')
    GetPromoted = ChoiceItem('get_promoted', 'I want to get promoted')
    ImproveCurrentRole = ChoiceItem('improve_current_role', 'I want to improve at my current role')
    Other = ChoiceItem('other', 'Other')


class ProductTypes(DjangoChoices):
    """
    Product types to be used in retrieving skills.
    """

    Course = ChoiceItem('course', 'Course')
    Program = ChoiceItem('program', 'Program')
    XBlock = ChoiceItem('xblock', 'XBlock')
    XBlockData = ChoiceItem('xblock_data', 'XBlockData')
