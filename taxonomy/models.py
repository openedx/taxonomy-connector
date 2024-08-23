# -*- coding: utf-8 -*-
"""
ORM Models for the taxonomy application.
"""
from __future__ import unicode_literals

import logging
import uuid

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from solo.models import SingletonModel

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from model_utils.models import TimeStampedModel

from taxonomy.choices import UserGoal
from taxonomy.providers.utils import get_course_metadata_provider

LOGGER = logging.getLogger(__name__)


class Skill(TimeStampedModel):
    """
    Skills that can be acquired by a learner.

    .. no_pii:
    """

    external_id = models.CharField(
        max_length=255,
        blank=False,
        null=False,
        unique=True,
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
    description = models.TextField(
        blank=True,
        help_text='A short description for the skill received from API.',
        default='',
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
    category = models.ForeignKey(
        'SkillCategory',
        on_delete=models.deletion.SET_NULL,
        null=True,
        blank=True,
        help_text=_('Category this skill belongs to.'),
        related_query_name='skills',
    )
    subcategory = models.ForeignKey(
        'SkillSubCategory',
        on_delete=models.deletion.SET_NULL,
        null=True,
        blank=True,
        help_text=_('Sub category this skill belongs to.'),
        related_query_name='skills',
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


class CourseRunXBlockSkillsTracker(TimeStampedModel):
    """
    Model to track completion of tagging of xblocks in courses.

    .. no_pii:
    """

    course_run_key = models.CharField(
        unique=True,
        max_length=255,
        help_text=_('Course run key of the course under which all xblocks were tagged.')
    )

    class Meta:
        """
        Meta configuration for XBlockSkills model.
        """

        verbose_name = 'Course run xblock skills tracker'
        verbose_name_plural = 'Course run xblock skills tracker'
        ordering = ('created', )
        app_label = 'taxonomy'

    def __str__(self):
        """
        Create a human-readable string representation of the object.
        """
        return '<CourseRunXBlockSkillsTracker course_run_key="{}">'.format(self.course_run_key)

    def __repr__(self):
        """
        Create a unique string representation of the object.
        """
        return '<CourseRunXBlockSkillsTracker id="{0}">'.format(self.id)


class XBlockSkills(TimeStampedModel):
    """
    Skills that will be learnt by completing xblock.

    .. no_pii:
    """

    usage_key = models.CharField(
        unique=True,
        db_index=True,
        max_length=255,
        help_text=_('The key of the xblock whose text was used for skills extraction.')
    )
    skills = models.ManyToManyField(
        Skill,
        through='XBlockSkillData',
        help_text=_(
            'The ID of the skill extracted for the xblock.'
        )
    )
    requires_verification = models.BooleanField(
        default=True,
        help_text=_('Indicates whether skills applied to this block requires verification from users'),
    )
    auto_processed = models.BooleanField(
        default=False,
        help_text=_('Indicates whether the text from this block was already processed'),
    )
    hash_content = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_('Hashed text content useful for checking if content has changed')
    )

    class Meta:
        """
        Meta configuration for XBlockSkills model.
        """

        verbose_name = 'XBlock Skills'
        verbose_name_plural = 'XBlock Skills'
        ordering = ('created', )
        app_label = 'taxonomy'

    def __str__(self):
        """
        Create a human-readable string representation of the object.
        """
        return '<XBlockSkills usage_key="{}">'.format(self.usage_key)

    def __repr__(self):
        """
        Create a unique string representation of the object.
        """
        return '<XBlockSkills id="{0}">'.format(self.id)


class XBlockSkillData(TimeStampedModel):
    """
    Skills that will be learnt by completing xblock.

    .. no_pii:
    """

    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    xblock = models.ForeignKey(XBlockSkills, on_delete=models.CASCADE)
    verified_count = models.IntegerField(
        blank=True,
        null=True,
        default=0,
        help_text=_('Number of times learners verified this skill')
    )
    ignored_count = models.IntegerField(
        blank=True,
        null=True,
        default=0,
        help_text=_('Number of times learners ignored giving feedback for this skill')
    )
    verified = models.BooleanField(
        default=False,
        help_text=_('Indicates that this skill has been finalized for this block'),
    )
    confidence = models.FloatField(
        blank=False,
        help_text=_(
            'The extraction confidence threshold used for the skills extraction.'
        )
    )
    is_blacklisted = models.BooleanField(
        help_text=_('Blacklist this xblock skill, useful to handle false positives.'),
        default=False, db_index=True
    )

    class Meta:
        """
        Meta configuration for XBlockSkillData model.
        """

        verbose_name = 'Xblock Skill data'
        verbose_name_plural = 'Xblock Skill data'
        ordering = ('created', )
        app_label = 'taxonomy'
        unique_together = ('xblock', 'skill')
        indexes = [
            models.Index(fields=['created']),
        ]

    def __str__(self):
        """
        Create a human-readable string representation of the object.
        """
        return '<XBlockSkillData usage_key="{}" skill="{}" verified="{}">'.format(
            self.xblock.usage_key,
            self.skill.name,
            self.verified,
        )

    def __repr__(self):
        """
        Create a unique string representation of the object.
        """
        return '<XBlockSkillData id="{0}">'.format(self.id)


class CourseSkills(TimeStampedModel):
    """
    Skills that will be learnt by taking the course.

    .. no_pii:
    """

    course_key = models.CharField(
        max_length=255,
        help_text=_('The key of the course whose text was used for skills extraction.')
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
    is_blacklisted = models.BooleanField(
        help_text=_('Blacklist this course skill, useful to handle false positives.'),
        default=False,
    )

    class Meta:
        """
        Meta configuration for CourseSkills model.
        """

        verbose_name = 'Course Skill'
        verbose_name_plural = 'Course Skills'
        ordering = ('created', )
        app_label = 'taxonomy'
        unique_together = ('course_key', 'skill')

    def __str__(self):
        """
        Create a human-readable string representation of the object.
        """
        return '<CourseSkills name="{}" course_key="{}">'.format(self.skill.name, self.course_key)

    def __repr__(self):
        """
        Create a unique string representation of the object.
        """
        return '<CourseSkills id="{0}" skill="{1!r}">'.format(self.id, self.skill)


class ProgramSkill(TimeStampedModel):
    """
    Skills that will be learnt by taking the program.

    .. no_pii:
    """

    program_uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        help_text=_('The uuid of the program whose title would be used for skill(s) extraction.')
    )
    skill = models.ForeignKey(
        Skill,
        blank=False,
        null=False,
        on_delete=models.deletion.CASCADE,
        help_text=_(
            'The ID of the skill extracted for the program.'
        )
    )
    confidence = models.FloatField(
        help_text=_(
            'The extraction confidence threshold used for the skills extraction.'
        )
    )
    is_blacklisted = models.BooleanField(
        help_text=_('Blacklist this program skill, useful to handle false positives.'),
        default=False,
    )

    class Meta:
        """
        Meta configuration for ProgramSkill model.
        """

        verbose_name = 'Program Skill'
        verbose_name_plural = 'Program Skills'
        ordering = ('created', )
        app_label = 'taxonomy'
        unique_together = ('program_uuid', 'skill')

    def __str__(self):
        """
        Create a human-readable string representation of the object.
        """
        return '<ProgramSkill name="{}" program_uuid="{}">'.format(self.skill.name, self.program_uuid)

    def __repr__(self):
        """
        Create a unique string representation of the object.
        """
        return '<ProgramSkill id="{0}" skill="{1!r}">'.format(self.id, self.skill)


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


class RefreshXBlockSkillsConfig(SingletonModel):
    """
    Configuration for the refresh_xblock_skills management command.

    .. no_pii:
    """

    class Meta:
        """
        Meta configuration for RefreshXBlockSkillsConfig model.
        """

        app_label = 'taxonomy'
        verbose_name = 'refresh_xblock_skills argument'

    arguments = models.TextField(
        blank=True,
        help_text='Useful for manually running a Jenkins job. Specify like "--course=key1 --course=key2".',
        default='',
    )

    def __str__(self):
        """
        Create a human-readable string representation of the object.
        """
        return '<RefreshXBlockSkillsConfig arguments="{}">'.format(self.arguments)

    def __repr__(self):
        """
        Create a unique string representation of the object.
        """
        return '<RefreshXBlockSkillsConfig id="{}">'.format(self.id)


class RefreshProgramSkillsConfig(SingletonModel):
    """
    Configuration for the refresh_program_skills management command.

    .. no_pii:
    """

    class Meta:
        """
        Meta configuration for RefreshProgramSkillsConfig model.
        """

        app_label = 'taxonomy'
        verbose_name = 'Refresh Program Skills Configuration'

    arguments = models.TextField(
        blank=True,
        help_text='Useful for manually running a Jenkins job. Specify like "--program=uuid --program=uuid".',
        default='',
    )

    def __str__(self):
        """
        Create a human-readable string representation of the object.
        """
        return '<RefreshProgramSkillsConfig arguments="{}">'.format(self.arguments)

    def __repr__(self):
        """
        Create a unique string representation of the object.
        """
        return '<RefreshProgramSkillsConfig id="{}">'.format(self.id)


class Job(TimeStampedModel):
    """
    Jobs available.

    .. no_pii:
    """

    external_id = models.CharField(
        max_length=255,
        unique=True,
        help_text=_(
            'The external identifier for the job received from API.'
        )
    )
    name = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=False,
        help_text=_(
            'The title of job.'
        )
    )
    description = models.TextField(default='', help_text='AI generated job description.')

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
        return '<Job id="{}" name="{}" external_id="{}" description="{}">'.format(
            self.id,
            self.name,
            self.external_id,
            self.description
        )

    def get_whitelisted_job_skills(self, prefetch_skills=True):
        """
        Get a QuerySet of all the whitelisted skills associated with the job.
        """
        job_skill_qs = JobSkills.get_whitelisted_job_skill_qs().filter(job=self)
        industry_job_skill_qs = IndustryJobSkill.get_whitelisted_job_skill_qs().filter(job=self)
        if prefetch_skills:
            job_skill_qs = job_skill_qs.select_related('skill')
            industry_job_skill_qs = industry_job_skill_qs.select_related('skill')
        return job_skill_qs, industry_job_skill_qs

    def get_blacklisted_job_skills(self, prefetch_skills=True):
        """
        Get a QuerySet of all the whitelisted skills associated with the job.
        """
        job_skill_qs = JobSkills.get_blacklist_job_skill_qs().filter(job=self)
        industry_job_skill_qs = IndustryJobSkill.get_blacklist_job_skill_qs().filter(job=self)

        if prefetch_skills:
            job_skill_qs = job_skill_qs.select_related('skill')
            industry_job_skill_qs = industry_job_skill_qs.select_related('skill')
        return job_skill_qs, industry_job_skill_qs

    def blacklist_job_skills(self, skill_ids):
        """
        Black list all job skills with the given skill ids.

        Arguments:
            skill_ids (list<int>): A list of Skill ids that should be black list for the current job.
        """
        self.jobskills_set.filter(skill__id__in=skill_ids).update(is_blacklisted=True)
        self.industryjobskill_set.filter(skill__id__in=skill_ids).update(is_blacklisted=True)

    def whitelist_job_skills(self, skill_ids):
        """
        Remove all job skills with the given skill ids from the blacklist.

        Arguments:
            skill_ids (list<int>): A list of Skill ids that should be removed from the blacklist.
        """
        self.jobskills_set.filter(skill__id__in=skill_ids).update(is_blacklisted=False)
        self.industryjobskill_set.filter(skill__id__in=skill_ids).update(is_blacklisted=False)


class JobPath(TimeStampedModel):
    """
    Current job to new job path description.

    .. no_pii:
    """

    current_job = models.ForeignKey(
        Job,
        to_field='external_id',
        related_name='+',
        blank=False,
        null=False,
        on_delete=models.deletion.CASCADE,
        help_text=_('The external id of the current job.')
    )

    future_job = models.ForeignKey(
        Job,
        to_field='external_id',
        related_name='+',
        blank=False,
        null=False,
        on_delete=models.deletion.CASCADE,
        help_text=_('The external id of the future job.')
    )

    description = models.TextField(help_text='AI generated current job to future job path description.')

    class Meta:
        """
        Metadata for the JobPath model.
        """

        verbose_name = 'Job Path Description'
        verbose_name_plural = 'Job Path Descriptions'
        ordering = ('created',)
        unique_together = ('current_job', 'future_job')
        app_label = 'taxonomy'

    def clean(self):
        """
        Add validation to raise an exception if current and future jobs are same.
        """
        if self.current_job.external_id == self.future_job.external_id:
            raise ValidationError('Current and Future jobs can not be same.')

    def save(self, *args, **kwargs):
        """
        Override to ensure that model.clean is always called.
        """
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        """
        Create a human-readable string representation of the object.
        """
        return 'Job path from "{}" to "{}" is "{}")'.format(self.current_job, self.future_job, self.description)

    def __repr__(self):
        """
        Create a unique string representation of the object.
        """
        return 'JobPath(current_job="{}", future_job="{}", description="{}")'.format(
            self.current_job, self.future_job, self.description
        )


class BaseJobSkill(TimeStampedModel):
    """
    A Base Table to hold association between Skill-Job.

    .. no_pii:
    """

    skill = models.ForeignKey(
        Skill,
        on_delete=models.deletion.CASCADE,
        help_text=_(
            'Skill associated with the job-skill.'
        )
    )

    job = models.ForeignKey(
        Job,
        blank=False,
        null=False,
        on_delete=models.deletion.CASCADE,
        help_text=_(
            'Job associated with the job-skill.'
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
    is_blacklisted = models.BooleanField(default=False, help_text=_('Should this job skill be ignored?'))

    class Meta:
        """
        Metadata for the BaseJobSkill model.
        """

        abstract = True

    @classmethod
    def get_whitelisted_job_skill_qs(cls):
        """
        Get a QuerySet of whitelisted job skills.

        White listed job skills are job skills with `is_blacklisted=False`.
        """
        return cls.objects.filter(is_blacklisted=False)

    @classmethod
    def get_blacklist_job_skill_qs(cls):
        """
        Get a QuerySet of whitelisted job skills.

        White listed job skills are job skills with `is_blacklisted=False`.
        """
        return cls.objects.filter(is_blacklisted=True)


class JobSkills(BaseJobSkill):
    """
    Table to hold association between Skill-Job.

    .. no_pii:
    """

    class Meta:
        """
        Metadata for the JobSkills model.
        """

        verbose_name = 'Job Skill'
        verbose_name_plural = 'Job Skills'
        ordering = ('created',)
        app_label = 'taxonomy'
        unique_together = ('job', 'skill')

    def __str__(self):
        """
        Create a human-readable string representation of the object.
        """
        return '<JobSkills job="{}" skill="{}" significance="{}">'.format(
            self.job.name, self.skill.name, self.significance
        )

    def __repr__(self):
        """
        Create a unique string representation of the object.
        """
        return '<JobSkills id={} job="{}" skill="{}" significance="{}">'.format(
            self.id, self.job.name, self.skill.name, self.significance
        )


class IndustryJobSkill(BaseJobSkill):
    """
    Table to hold association between Industry-Skill-Job. A None Industry means record is not industry specific.

    .. no_pii:
    """

    industry = models.ForeignKey(
        'Industry',
        on_delete=models.deletion.CASCADE,
        help_text=_(
            'Industry associated with the job-skill.'
        )
    )

    class Meta:
        """
        Metadata for the JobSkillsIndustry model.
        """

        verbose_name = 'Industry Job Skill'
        verbose_name_plural = 'Industry Job Skills'
        ordering = ('created',)
        app_label = 'taxonomy'
        unique_together = ('industry', 'job', 'skill')

    def __str__(self):
        """
        Create a human-readable string representation of the object.
        """
        return '<IndustryJobSkills industry="{}" job="{}" skill="{}" significance="{}">'.format(
            self.industry.name, self.job.name, self.skill.name, self.significance
        )

    def __repr__(self):
        """
        Create a unique string representation of the object.
        """
        return '<IndustryJobSkills id={} industry="{}" job="{}" skill="{}" significance="{}">'.format(
            self.id, self.industry.name, self.job.name, self.skill.name, self.significance
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
        unique=True,
        on_delete=models.deletion.CASCADE,
        help_text=_(
            'The ID of the job to filter job postings by.'
        )
    )

    median_salary = models.FloatField(
        blank=True,
        null=True,
        help_text=_(
            'The median annual salary (in USD) advertised on job postings for the job.'
        ),
    )

    median_posting_duration = models.IntegerField(
        blank=True,
        null=True,
        help_text=_(
            'The median duration of closed job postings. Duration is measured in days.'
        )
    )

    unique_postings = models.IntegerField(
        blank=True,
        null=True,
        help_text=_(
            'The number of unique monthly active job postings.'
        )
    )

    unique_companies = models.IntegerField(
        blank=True,
        null=True,
        help_text=_(
            'The number of unique companies represented in your filtered set of postings.'
        )
    )

    class Meta:
        """
        Metadata for the JobPostings model.
        """

        verbose_name = 'Job Posting'
        verbose_name_plural = 'Job Postings'
        ordering = ('created',)
        app_label = 'taxonomy'

    def __str__(self):
        """
        Create a human-readable string representation of the object.
        """
        return '<Job postings for job: {}, have a median_salary: ${}, median_posting_duration: {}, ' \
               'unique_postings: {}, unique hiring companies: {} >'.format(
                   self.job.name, self.median_salary, self.median_posting_duration, self.unique_postings,
                   self.unique_companies)

    def __repr__(self):
        """
        Return string representation.
        """
        return '<JobPosting id="{0}" job="{1!r}" median_salary="${2!r}" median_posting_duration="{3!r}" ' \
            'unique_postings="{4!r} unique_companies={5!r}">'.format(
                self.id, self.job, self.median_salary, self.median_posting_duration, self.unique_postings,
                self.unique_companies)


class Translation(TimeStampedModel):
    """
    Model to save translated descriptions.

    .. no_pii:
    """

    source_model_name = models.CharField(
        max_length=255,
        help_text=_(
            'The name of the model to which the source belongs e:g Course.'
        )
    )

    source_model_field = models.CharField(
        max_length=255,
        help_text=_(
            'The name of the source field to be translated e:g course description.'
        )
    )

    source_record_identifier = models.CharField(
        max_length=255,
        help_text=_('The identifier of the source record e:g course key.')
    )

    source_text = models.TextField(
        blank=True,
        null=True,
        help_text=_(
            'The source text to be translated.'
        )
    )

    source_language = models.CharField(
        blank=True,
        null=True,
        max_length=8,
        help_text=_(
            'The original language of the source text before translation e:g Spanish.'
        )
    )

    translated_text = models.TextField(
        blank=True,
        null=True,
        help_text=_(
            'The translated source text.'
        )
    )

    translated_text_language = models.CharField(
        blank=True,
        null=True,
        max_length=8,
        help_text=_(
            'The language of the source text to which it is translated e:g English.'
        )
    )

    class Meta:
        """
        Metadata for the Translation model.
        """

        ordering = ('created',)
        app_label = 'taxonomy'
        unique_together = ('source_record_identifier', 'source_model_name', 'source_model_field',)

    def __str__(self):
        """
        Create a human-readable string representation of the object.
        """
        return '<Translation for source_record_identifier={} source_language={} translated_text_language={}>'.format(
            self.source_record_identifier,
            self.source_language,
            self.translated_text_language
        )

    def __repr__(self):
        """
        Create a unique string representation of the object.
        """
        return '<Translation source_model_name="{}" source_model_field="{}" source_record_identifier="{}" ' \
               'source_text="{}" source_language="{}" translated_text="{}" translated_text_language="{}">'.format(
                   self.source_model_name, self.source_model_field, self.source_record_identifier, self.source_text,
                   self.source_language, self.translated_text, self.translated_text_language)


class SkillCategory(TimeStampedModel):
    """
    Model to save category of a skill.

    .. no_pii:
    """

    id = models.IntegerField(  # pylint: disable=invalid-name
        primary_key=True,
        help_text=_(
            'Category id, this is the same id as received from EMSI API.'
        )
    )
    name = models.CharField(
        max_length=255,
        help_text=_(
            'The name of the category.'
        )
    )

    def __str__(self):
        """
        Create a human-readable string representation of the object.
        """
        return '<SkillCategory id="{}" name="{}">'.format(self.id, self.name)

    def __repr__(self):
        """
        Create a unique string representation of the object.
        """
        return self.__str__()

    class Meta:
        """
        Meta configuration for Skill model.
        """

        ordering = ('id', )
        app_label = 'taxonomy'
        verbose_name = 'Skill Category'
        verbose_name_plural = 'Skill Categories'


class SkillSubCategory(TimeStampedModel):
    """
    Model to save subcategory of a skill.

    .. no_pii:
    """

    id = models.IntegerField(  # pylint: disable=invalid-name
        primary_key=True,
        help_text=_(
            'Sub category id, this is the same id as received from EMSI API.'
        )
    )
    name = models.CharField(
        max_length=255,
        help_text=_(
            'The name of the subcategory.'
        )
    )
    category = models.ForeignKey(SkillCategory, on_delete=models.CASCADE, related_query_name='sub_categories')

    def __str__(self):
        """
        Create a human-readable string representation of the object.
        """
        return '<SkillSubCategory id="{}" name="{}" category="{}">'.format(self.id, self.name, self.category.name)

    def __repr__(self):
        """
        Create a unique string representation of the object.
        """
        return '<SkillSubCategory id="{}" name="{}">'.format(self.id, self.name)

    class Meta:
        """
        Meta configuration for Skill model.
        """

        ordering = ('id', )
        app_label = 'taxonomy'
        verbose_name = 'Skill Subcategory'
        verbose_name_plural = 'Skill Subcategories'


class SkillsQuiz(TimeStampedModel):
    """
    Model for storing skills quiz information filled out by a user.

    .. no_pii:
    """

    username = models.CharField(_("username"), max_length=150)
    skills = models.ManyToManyField(Skill, null=True, blank=True)
    current_job = models.ForeignKey(
        Job, on_delete=models.SET_NULL, related_name='current_job_skills_quiz', null=True, blank=True
    )
    future_jobs = models.ManyToManyField(Job, related_name='future_jobs_skills_quiz', blank=True)
    goal = models.CharField(max_length=64, choices=UserGoal.choices)

    def __str__(self):
        """
        Create a human-readable string representation of the object.
        """
        return '<SkillsQuiz id="{}" user="{}">'.format(self.id, self.username)

    def __repr__(self):
        """
        Create a unique string representation of the object.
        """
        return '<SkillsQuiz id="{}" user="{}">'.format(self.id, self.username)

    class Meta:
        """
        Meta configuration for Skill model.
        """

        ordering = ('id', )
        app_label = 'taxonomy'
        verbose_name = 'Skill Quiz'
        verbose_name_plural = 'Skill Quizzes'


class Industry(models.Model):
    """
    Model for storing industry NAICS2 data.

    .. no_pii:
    """

    name = models.CharField(_("Industry Name"), max_length=256)
    code = models.IntegerField()

    def __str__(self):
        """
        Create a human-readable string representation of the object.
        """
        return '<Industry id="{}" name="{}">'.format(self.id, self.name)

    def __repr__(self):
        """
        Create a unique string representation of the object.
        """
        return '<Industry id="{}" code="{}">'.format(self.id, self.code)

    class Meta:
        """
        Meta configuration for Skill model.
        """

        ordering = ('id', )
        app_label = 'taxonomy'
        verbose_name = 'Industry'
        verbose_name_plural = 'Industries'


class B2CJobAllowList(models.Model):
    """
    Model for storing admin configuration for B2C Job Allowlist entries.

    .. no_pii:
    """

    job = models.ForeignKey(
        Job,
        to_field='external_id',
        related_name='+',
        blank=False,
        null=False,
        on_delete=models.deletion.CASCADE,
        help_text=_('The job to add to the allowlist for B2C Job listings.')
    )

    def __str__(self):
        """
        Create a human-readable string representation of the object.
        """
        return '<External Id = "{}" Job ="{}">'.format(self.job.external_id, self.job)

    def __repr__(self):
        """
        Create a unique string representation of the object.
        """
        return '<External Id = "{}" Job ="{}">'.format(self.job.external_id, self.job)

    class Meta:
        """
        Meta configuration for B2C Job Allow List model.
        """

        app_label = 'taxonomy'
        verbose_name = 'B2C Job Allow List entry'
        verbose_name_plural = 'B2C Job Allow List entries'


class SkillValidationConfiguration(TimeStampedModel):
    """
    Model to store the configuration for disabling skill validation for a course or organization.
    """

    course_key = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        unique=True,
        help_text=_('The course, for which skill validation is disabled.'),
    )
    organization = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        unique=True,
        help_text=_('The organization, for which skill validation is disabled.'),
    )

    def __str__(self):
        """
        Create a human-readable string representation of the object.
        """
        message = ''

        if self.course_key:
            message = f'Skill validation disabled for course: {self.course_key}'
        elif self.organization:
            message = f'Skill validation disabled for organization: {self.organization}'

        return message

    class Meta:
        """
        Meta configuration for SkillValidationConfiguration model.
        """

        constraints = [
            models.CheckConstraint(
                check=(
                    Q(course_key__isnull=False) &
                    Q(organization__isnull=True)
                ) | (
                    Q(course_key__isnull=True) &
                    Q(organization__isnull=False)
                ),
                name='either_course_or_org',
                # This only work on django >= 4.1
                # violation_error_message='Select either course or organization.'
            ),
        ]

        verbose_name = 'Skill Validation Configuration'
        verbose_name_plural = 'Skill Validation Configurations'

    def clean(self):
        """Override to add custom validation for course and organization fields."""
        if self.course_key:
            if not get_course_metadata_provider().is_valid_course(self.course_key):
                raise ValidationError({
                    'course_key': f'Course with key {self.course_key} does not exist.'
                })

        if self.organization:
            if not get_course_metadata_provider().is_valid_organization(self.organization):
                raise ValidationError({
                    'organization': f'Organization with key {self.organization} does not exist.'
                })

    # pylint: disable=no-member
    def validate_constraints(self, exclude=None):
        """
        Validate all constraints defined in Meta.constraints.

        NOTE: We override this method only to return a human readable message.
        We should remove this override once taxonomy-connector is updated to django 4.1
        On django >= 4.1, add violation_error_message in models.CheckConstraint with an appropriate message.
        """
        try:
            super().validate_constraints(exclude=exclude)
        except ValidationError as ex:
            raise ValidationError({'__all__': 'Add either course key or organization.'}) from ex

    def save(self, *args, **kwargs):
        """Override to ensure that custom validation is always called."""
        self.full_clean()
        return super().save(*args, **kwargs)

    @staticmethod
    def is_valid_course_run_key(course_run_key):
        """
        Check if the given course run key is in valid format.

        Arguments:
            course_run_key (str): Course run key
        """
        try:
            return True, CourseKey.from_string(course_run_key)
        except InvalidKeyError:
            LOGGER.error('[TAXONOMY_SKILL_VALIDATION_CONFIGURATION] Invalid course_run key: [%s]', course_run_key)

        return False, None

    @classmethod
    def is_disabled(cls, course_run_key) -> bool:
        """
        Check if skill validation is disabled for the given course run key.

        Arguments:
            course_run_key (str): Course run key

        Returns:
            bool: True if skill validation is disabled for the given course run key.
        """
        is_valid_course_run_key, course_run_locator = cls.is_valid_course_run_key(course_run_key)
        if not is_valid_course_run_key:
            return False

        if cls.objects.filter(organization=course_run_locator.org).exists():
            return True

        course_key = get_course_metadata_provider().get_course_key(course_run_key)
        if course_key and cls.objects.filter(course_key=course_key).exists():
            return True

        return False
