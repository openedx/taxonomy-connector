# -*- coding: utf-8 -*-
"""
ORM Models for the taxonomy application.
"""
from __future__ import unicode_literals

from solo.models import SingletonModel

from django.db import models
from django.utils.translation import ugettext as _

from model_utils.models import TimeStampedModel


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
            'The external identifier for the skill received from API.'
        )
    )
    name = models.CharField(
        max_length=255,
        blank=True,
        help_text=_(
            'The name of the skill.'
        )
    )
    info_url = models.URLField(
        verbose_name=_('Skill Information URL'),
        blank=True,
        help_text=_(
            'The url with more info for the skill.'
        )
    )
    type_id = models.CharField(
        max_length=255,
        blank=True,
        help_text=_(
            'The external type id for the skill received from API.'
        )
    )
    type_name = models.CharField(
        max_length=255,
        blank=True,
        help_text=_(
            'The external type name for the skill received from API.'
        )
    )

    def __str__(self):
        """
        Create a human-readable string representation of the object.
        """
        return '<Skill name="{}" external_id="{}">'.format(self.name, self.external_id)

    def __repr__(self):
        """
        Create a unique string representation of the object.
        """
        return '<Skill id="{}" name="{}">'.format(self.id, self.name)

    class Meta:
        """
        Meta configuration for Skill model.
        """

        ordering = ('created', )
        app_label = 'taxonomy'


class CourseSkills(TimeStampedModel):
    """
    Skills that will be learnt by taking the course.

    .. no_pii:
    """

    course_id = models.CharField(
        max_length=255,
        blank=False,
        help_text=_(
            'The ID of the course whose text was used for skills extraction.'
        )
    )
    skill = models.ForeignKey(
        Skill,
        blank=False,
        null=False,
        on_delete=models.deletion.CASCADE,
        help_text=_(
            'The ID of the skill extracted for the course.'
        )
    )
    confidence = models.FloatField(
        blank=False,
        help_text=_(
            'The extraction confidence threshold used for the skills extraction.'
        )
    )

    class Meta:
        """
        Meta configuration for CourseSkills model.
        """

        ordering = ('created', )
        app_label = 'taxonomy'

    def __str__(self):
        """
        Create a human-readable string representation of the object.
        """
        return '<Skill name="{}" course_id="{}">'.format(self.skill.name, self.course_id)

    def __repr__(self):
        """
        Create a unique string representation of the object.
        """
        return '<Skill id="{0}" skill="{1!r}">'.format(self.id, self.skill)


class BlacklistedCourseSkill(TimeStampedModel):
    """
    Course skills that are black listed to avoid false positives.

    .. no_pii:
    """

    course_id = models.CharField(
        max_length=255,
        help_text=_(
            'The course key belonging the course whose skill needs to be black-listed.'
        )
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.deletion.CASCADE,
        help_text=_(
            'The skill extracted for the course that needs to be black-listed.'
        )
    )

    class Meta:
        """
        Meta configuration for CourseSkills model.
        """

        ordering = ('created', )
        app_label = 'taxonomy'

    def __str__(self):
        """
        Create a human-readable string representation of the object.
        """
        return '<BlacklistedCourseSkill skill="{}" course_id="{}">'.format(self.skill.name, self.course_id)

    def __repr__(self):
        """
        Create a unique string representation of the object.
        """
        return '<BlacklistedCourseSkill id="{0}" skill="{1!r}">'.format(self.id, self.skill)


class RefreshCourseSkillsConfig(SingletonModel):
    """
    Configuration for the refresh_course_skills management command.

    .. no_pii:
    """

    class Meta:
        """
        Meta configuration for RefreshCourseSkillsConfig model.
        """

        app_label = 'taxonomy'
        verbose_name = 'refresh_course_skills argument'

    arguments = models.TextField(
        blank=True,
        help_text='Useful for manually running a Jenkins job. Specify like "--course=key1 --course=key2".',
        default='',
    )

    def __str__(self):
        """
        Create a human-readable string representation of the object.
        """
        return '<RefreshCourseSkillsConfig arguments="{}">'.format(self.arguments)

    def __repr__(self):
        """
        Create a unique string representation of the object.
        """
        return '<RefreshCourseSkillsConfig id="{}">'.format(self.id)


class Job(TimeStampedModel):
    """
    Jobs available.

    .. no_pii:
    """

    name = models.CharField(
        max_length=255,
        blank=False,
        help_text=_(
            'The title of job.'
        )
    )

    class Meta:
        """
        Metadata for the Job model.
        """

        ordering = ('created',)
        app_label = 'taxonomy'

    def __str__(self):
        """
        Create a human-readable string representation of the object.
        """
        return '<Job title={}>'.format(self.name)

    def __repr__(self):
        """
        Create a unique string representation of the object.
        """
        return '<Job id="{}" name="{}">'.format(self.id, self.name)


class JobSkills(TimeStampedModel):
    """
    Skills for a job.

    .. no_pii:
    """

    skill = models.ForeignKey(
        Skill,
        on_delete=models.deletion.CASCADE,
        help_text=_(
            'The skill required for the job.'
        )
    )

    job = models.ForeignKey(
        Job,
        blank=False,
        null=False,
        on_delete=models.deletion.CASCADE,
        help_text=_(
            'The ID of the job title extracted for the skill.'
        )
    )

    significance = models.FloatField(
        blank=False,
        help_text=_(
            'The significance of skill for the job.'
        )
    )

    unique_postings = models.FloatField(
        blank=False,
        help_text=_(
            'The unique_postings threshold of skill for the job.'
        )
    )

    class Meta:
        """
        Metadata for the JobSkills model.
        """

        ordering = ('created',)
        app_label = 'taxonomy'

    def __str__(self):
        """
        Create a human-readable string representation of the object.
        """
        return '<Skill name="{}" significance="{}" unique_postings="{}">'.format(
            self.skill.name, self.significance, self.unique_postings
        )

    def __repr__(self):
        """
        Create a unique string representation of the object.
        """
        return '<Skill id="{0}" name="{1}" job="{2!r}">'.format(
            self.id, self.skill.name, self.job,
        )


class JobPostings(TimeStampedModel):
    """
    Postings for a job.

    .. no_pii:
    """

    job = models.ForeignKey(
        Job,
        blank=False,
        null=False,
        on_delete=models.deletion.CASCADE,
        help_text=_(
            'The ID of the job to filter job postings by.'
        )
    )

    median_salary = models.FloatField(
        blank=False,
        help_text=_(
            'The median annual salary advertised on job postings for the job.'
        )
    )

    median_posting_duration = models.IntegerField(
        blank=False,
        help_text=_(
            'The median duration of closed job postings. Duration is measured in days.'
        )
    )

    unique_postings = models.IntegerField(
        blank=False,
        help_text=_(
            'The number of unique monthly active job postings.'
        )
    )

    unique_companies = models.IntegerField(
        blank=False,
        help_text=_(
            'The number of unique companies represented in your filtered set of postings.'
        )
    )

    class Meta:
        """
        Metadata for the JobPostings model.
        """

        ordering = ('created',)
        app_label = 'taxonomy'

    def __str__(self):
        """
        Create a human-readable string representation of the object.
        """
        return '<Job postings for job: {}, have a median_salary: {}, median_posting_duration: {}, unique_postings: {}' \
               ', unique hiring companies: {} >'.format(
                   self.job.name, self.median_salary, self.median_posting_duration, self.unique_postings,
                   self.unique_companies)

    def __repr__(self):
        """
        Return string representation.
        """
        return '<JobPosting id="{0}" job="{1!r}" median_salary="{2!r}" median_posting_duration="{3!r}" ' \
            'unique_postings="{4!r} unique_companies={5!r}">'.format(
                self.id, self.job, self.median_salary, self.median_posting_duration, self.unique_postings,
                self.unique_companies)
