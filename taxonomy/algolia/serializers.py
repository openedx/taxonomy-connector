# -*- coding: utf-8 -*-
"""
Serializers to convert db data to a dictionary that algolia can understand.

This module depends on serializers provided by django-rest-framework.
"""

from rest_framework import serializers

from taxonomy.algolia.constants import EMBEDDED_OBJECT_LENGTH_CAP
from taxonomy.models import Job, JobPostings, JobSkills, IndustryJobSkill


class JobPostingSerializer(serializers.ModelSerializer):
    """
    JobPosting serializer for algolia index.

    This serializer will contain all of the metadata related to the job posting.
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

    This serializer will contain all of the metadata related to jobs and will also included metadata for skills and
    courses.
    """
    skills = serializers.SerializerMethodField()
    job_postings = serializers.SerializerMethodField()

    # ref: https://www.algolia.com/doc/api-client/methods/indexing/#the-objectid
    objectID = serializers.SerializerMethodField()  # required by Algolia, e.g. "job-{external_id}"

    industry_names = serializers.SerializerMethodField()
    industries = serializers.SerializerMethodField()
    similar_jobs = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = ('id', 'external_id', 'name', 'skills', 'job_postings', 'objectID', 'industry_names',
                  'industries', 'similar_jobs')
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
        qs = JobSkills.objects.filter(job=obj).select_related('skill')[:EMBEDDED_OBJECT_LENGTH_CAP]
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
        return list(IndustryJobSkill.objects.filter(job=obj)
                    .order_by("industry__name")
                    .values_list('industry__name', flat=True).distinct())

    def get_industries(self, obj):
        """
        Get a list of industries associated with a job and their skills.
        Arguments:
            obj (Job): Job instance whose industries need to be fetched.
        """
        industries = []
        job_industries = list(IndustryJobSkill.objects.filter(job=obj).order_by("industry__name").
                              values_list('industry__name', flat=True).distinct())
        for industry_name in job_industries:
            industry_skills = self.context.get('industry_skills')[industry_name]
            industries.append({'name': industry_name, 'skills': industry_skills})
        return industries

    @staticmethod
    def extract_similar_jobs(recommendations, name):
        """
        Extract similar jobs from recommendations.

        Arguments:
            recommendations (list): List containing dictionaries of job names and recommendations.
            name (str): Name of the job for which recommendations are being extracted.
        """
        similar_jobs = []
        for recommendation in recommendations:
            if recommendation['name'] == name:
                similar_jobs = recommendation['similar_jobs']
                break
        return similar_jobs

    def get_similar_jobs(self, obj):
        """
        Get a list of recommendations.
        """
        recommendations_data = self.context.get('jobs_with_recommendations', None)
        return self.extract_similar_jobs(recommendations_data, obj.name)


class JobSkillSerializer(serializers.ModelSerializer):
    """
    JobSkill serializer for algolia index.

    This serializer will contain all of the metadata related to the skill and will also included metadata for skills and
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
