# -*- coding: utf-8 -*-
"""
Serializers to convert db data to a dictionary that algolia can understand.

This module depends on serializers provided by django-rest-framework.
"""

from rest_framework import serializers

from taxonomy.algolia.constants import EMBEDDED_OBJECT_LENGTH_CAP
from taxonomy.constants import JOB_SOURCE_COURSE_SKILL, JOB_SOURCE_INDUSTRY
from taxonomy.models import B2CJobAllowList, IndustryJobSkill, Job, JobPostings, JobSkills


class JobPostingSerializer(serializers.ModelSerializer):
    """
    JobPosting serializer for algolia index.

    This serializer will contain all the metadata related to the job posting.
    """
    class Meta:
        model = JobPostings
        fields = (
            'job_id', 'median_salary', 'median_posting_duration', 'unique_postings', 'unique_companies',
        )
        read_only_fields = fields


class JobSerializer(serializers.ModelSerializer):
    """
    Job serializer for algolia index.

    This serializer will contain all the metadata related to jobs and will also include metadata for skills and
    courses.
    """
    skills = serializers.SerializerMethodField()
    job_postings = serializers.SerializerMethodField()

    # ref: https://www.algolia.com/doc/api-client/methods/indexing/#the-objectid
    objectID = serializers.SerializerMethodField()  # required by Algolia, e.g. "job-{external_id}"

    industry_names = serializers.SerializerMethodField()
    industries = serializers.SerializerMethodField()
    similar_jobs = serializers.SerializerMethodField()
    b2c_opt_in = serializers.SerializerMethodField(source="get_b2c_opt_in")
    job_sources = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = (
            'id', 'external_id', 'name', 'description', 'skills', 'job_postings', 'objectID', 'industry_names',
            'industries', 'similar_jobs', 'b2c_opt_in', 'job_sources',
        )
        read_only_fields = fields

    def get_objectID(self, obj):  # pylint: disable=invalid-name
        """
        Construct a unique job id for algolia.

        Arguments:
            obj (Job): Job instance whose objectId needs to be formatted.
        """
        return 'job-{}'.format(obj.external_id)

    def get_skills(self, obj):
        """
        Get a list of skills associated with the job.

        This skill dict will also include extra fields that define the relationship of a job and skill, such as
        `significance`, `unique_postings` etc.

        Arguments:
            obj (Job): Job instance whose skills need to be fetched.
        """
        # We only need to fetch up-to 20 skills per job.
        qs = JobSkills.get_whitelisted_job_skill_qs().filter(
            job=obj
        ).select_related(
            'skill'
        )[:EMBEDDED_OBJECT_LENGTH_CAP]
        serializer = JobSkillSerializer(qs, many=True)
        return serializer.data

    def get_job_postings(self, obj):
        """
        Get a list of job postings associated with the job.

        Arguments:
            obj (Job): Job instance whose job postings need to be fetched.
        """
        # We only need to fetch up-to 20 job postings per job.
        qs = JobPostings.objects.filter(job=obj)[:EMBEDDED_OBJECT_LENGTH_CAP]
        serializer = JobPostingSerializer(qs, many=True)
        return serializer.data

    def get_industry_names(self, obj):
        """
        Get a list of industry names associated with the job.

        Arguments:
            obj (Job): Job instance whose industries need to be fetched.
        """
        return list(
            IndustryJobSkill.get_whitelisted_job_skill_qs().filter(
                job=obj
            ).order_by(
                'industry__name'
            ).values_list(
                'industry__name', flat=True
            ).distinct()
        )

    def get_industries(self, obj):
        """
        Get a list of industries associated with a job and their skills.
        Arguments:
            obj (Job): Job instance whose industries need to be fetched.
        """
        industries = []
        job_industries = list(
            IndustryJobSkill.get_whitelisted_job_skill_qs().filter(
                job=obj
            ).order_by(
                'industry__name'
            ).values_list(
                'industry__name', flat=True
            ).distinct()
        )
        for industry_name in job_industries:
            industry_skills = self.context.get('industry_skills')[industry_name]
            industries.append({'name': industry_name, 'skills': industry_skills})
        return industries

    def get_similar_jobs(self, obj):
        """
        Get a list of recommendations.
        """
        jobs_data = self.context.get('jobs_data', {})
        return jobs_data[obj.name]['similar_jobs']

    def get_b2c_opt_in(self, obj):
        """
        Checks to see if the job is present on our job allowlist. This attribute will be primarily used to filter the
        list of available jobs a learner can select from in the B2C Skills Builder.

        Arguments:
            obj (Job): Job instance, used so we can compare its external id to the items on the allowlist

        Returns:
            True if the job is listed on the allowlist, False if not.
        """
        return B2CJobAllowList.objects.filter(job=obj).exists()

    def get_job_sources(self, obj):
        """
        Get the source of the job in our system. i.e. if it was populated because of a course skill or industry data.
        """
        jobs_having_job_skills = self.context.get('jobs_having_job_skills', set())
        jobs_having_industry_skills = self.context.get('jobs_having_industry_skills', set())
        job_sources = []
        if obj.id in jobs_having_job_skills:
            job_sources.append(JOB_SOURCE_COURSE_SKILL)
        if obj.id in jobs_having_industry_skills:
            job_sources.append(JOB_SOURCE_INDUSTRY)
        return job_sources


class JobSkillSerializer(serializers.ModelSerializer):
    """
    JobSkill serializer for algolia index.

    This serializer will contain all the metadata related to the skill and will also include metadata for skills and
    courses.
    """
    external_id = serializers.CharField(source='skill.external_id', default=None)
    name = serializers.CharField(source='skill.name', default=None)
    description = serializers.CharField(source='skill.description', default=None)
    info_url = serializers.URLField(source='skill.info_url', default=None)
    type_id = serializers.CharField(source='skill.type_id', default=None)
    type_name = serializers.CharField(source='skill.type_name', default=None)

    class Meta:
        model = JobSkills
        fields = (
            'significance', 'unique_postings', 'external_id', 'name', 'description',
            'info_url', 'type_id', 'type_name',
        )
        read_only_fields = fields
