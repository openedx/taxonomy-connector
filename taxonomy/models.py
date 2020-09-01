# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from model_utils.models import TimeStampedModel
from django.utils.translation import ugettext as _


class Skill(models.Model):
    """
    Skills that can be acquired by a learner.

    .. no_pii:
    """
    external_id = models.CharField(
        max_length=255,
        blank=False,
        null=False,
        help_text=_(
            "The external identifier for the skill received from API."
        )
    )
    name = models.CharField(
        max_length=255,
        blank=True,
        help_text=_(
            "The name of the skill."
        )
    )
    info_url = models.URLField(
        verbose_name=_('Skill Information URL'),
        blank=True,
        help_text=_(
            "The url with more info for the skill."
        )
    )
    type_id = models.CharField(
        max_length=255,
        blank=True,
        help_text=_(
            "The external type id for the skill received from API."
        )
    )
    type_name = models.CharField(
        max_length=255,
        blank=True,
        help_text=_(
            "The external type name for the skill received from API."
        )
    )

    def __str__(self):
        """
        Create a human-readable string representation of the object.
        """
        return '<Skill with name: {} and external id: {}'.format(self.name, self.external_id)

    def __repr__(self):
        """
        Return string representation.
        """
        return self.__str__()


class CourseSkills(TimeStampedModel):
    """
    Skills extraction from course text.

    .. no_pii:
    """

    course_id = models.CharField(
        max_length=255,
        blank=False,
        help_text=_(
            "The ID of the course whose text was used for skills extraction."
        )
    )
    skill = models.ForeignKey(
        Skill,
        blank=False,
        null=False,
        on_delete=models.deletion.CASCADE,
        help_text=_(
            "The ID of the skill extracted for the course."
        )
    )
    confidence = models.FloatField(
        blank=False,
        help_text=_(
            "The extraction confidence threshold used for the skills extraction."
        )
    )

    class Meta:
        ordering = ['created']

    def __str__(self):
        """
        Create a human-readable string representation of the object.
        """
        return '<Skill: {} extracted for course_id: {}>'.format(self.skill.name, self.course_id)

    def __repr__(self):
        """
        Return string representation.
        """
        return self.__str__()
