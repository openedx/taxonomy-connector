"""
This module contains taxonomy related signals handlers.
"""


from django.dispatch import receiver

from taxonomy.tasks import update_course_skills

from .signals import UPDATE_COURSE_SKILLS


@receiver(UPDATE_COURSE_SKILLS)
def handle_update_course_skills(sender, course_uuid, **kwargs):  # pylint: disable=unused-argument
    """
    Handle signal and trigger task to update course skills.
    """
    update_course_skills.delay([course_uuid])
