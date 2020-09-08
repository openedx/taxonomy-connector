# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from model_utils.models import TimeStampedModel
from django.utils.translation import ugettext as _
from solo.models import SingletonModel


class Skill(TimeStampedModel):
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

    class Meta:
        ordering = ['created']
        app_label = "taxonomy"


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
        app_label = "taxonomy"

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


class RefreshCourseSkillsConfig(SingletonModel):
    """
    Configuration for the refresh_course_skills management command.
    """
    class Meta:
        app_label = "taxonomy"
        verbose_name = 'refresh_course_skills argument'

    arguments = models.TextField(
        blank=True,
        help_text='Useful for manually running a Jenkins job. Specify like "--course=key1 --course=key2".',
        default='',
    )

    def __str__(self):
        return self.arguments


class Job(TimeStampedModel):
    """
    Jobs available.
    .. no_pii:
    """

    name = models.CharField(
        max_length=255,
        blank=False,
        help_text=_(
            "The title of job."
        )
    )

    class Meta:
        ordering = ['created']
        app_label = "taxonomy"

    def __str__(self):
        """
        Create a human-readable string representation of the object.
        """
        return '<Job skill title {}.'.format(self.name)

    def __repr__(self):
        """
        Return string representation.
        """
        return self.__str__()


class JobSkills(TimeStampedModel):
    """
    Skills for a job.
    .. no_pii:
    """
    name = models.CharField(
        max_length=255,
        blank=True,
        help_text=_(
            "The name of the skill required for the job."
        )
    )

    job = models.ForeignKey(
        Job,
        blank=False,
        null=False,
        on_delete=models.deletion.CASCADE,
        help_text=_(
            "The ID of the job title extracted for the skill."
        )
    )

    significance = models.FloatField(
        blank=False,
        help_text=_(
            "The significance of skill for the job."
        )
    )

    unique_postings = models.FloatField(
        blank=False,
        help_text=_(
            "The unique_postings threshold of skill for the job."
        )
    )

    class Meta:
        ordering = ['created']
        app_label = "taxonomy"

    def __str__(self):
        """
        Create a human-readable string representation of the object.
        """
        return '<Skill with name: {}, significance {} and unique_postings: {}'.format(self.name, self.significance,
                                                                                    self.unique_postings)

    def __repr__(self):
        """
        Return string representation.
        """
        return self.__str__()


class JobPostings(TimeStampedModel):
    """
    Job postings for a job.
    .. no_pii:
    """

    job = models.ForeignKey(
        Job,
        blank=False,
        null=False,
        on_delete=models.deletion.CASCADE,
        help_text=_(
            "The ID of the job to filter job postings by"
        )
    )

    median_salary = models.DecimalField(
        blank=False,
        null=False,
        decimal_places=2,
        max_digits=12,
        help_text=_(
            "The median annual salary advertised on job postings for the job."
        )
    )

    median_posting_duration = models.FloatField(
        blank=False,
        help_text=_(
            "The median duration of closed job postings. Duration is measured in days."
        )
    )

    unique_postings = models.FloatField(
        blank=False,
        help_text=_(
            "The number of unique monthly active job postings."
        )
    )

    unique_companies = models.FloatField(
        blank=False,
        help_text=_(
            "The number of unique companies represented in your filtered set of postings."
        )
    )

    class Meta:
        ordering = ['created']
        app_label = "taxonomy"

    def __str__(self):
        """
        Create a human-readable string representation of the object.
        """
        return '<Job postings for job: {}, have a median_salary: {}, median_posting_duration: {}, unique_postings: {}' \
               ', unique hiring companies: {} >'.format(
            self.job.name,
            self.median_salary,
            self.median_posting_duration,
            self.unique_postings,
            self.unique_companies
        )

    def __repr__(self):
        """
        Return string representation.
        """
        return '<Job postings for job: {}, id={}, median_salary={}, median_posting_duration={}, unique_postings={}, ' \
               'unique_companies={} >'.format(
            self.job.name,
            self.id,
            self.median_salary,
            self.median_posting_duration,
            self.unique_postings,
            self.unique_companies
        )
