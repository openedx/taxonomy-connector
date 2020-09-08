# -*- coding: utf-8 -*-
"""
Tests for the django management command `refresh_course_skills`.
"""

import mock
from pytest import mark

from django.core.management import call_command
from django.test import TestCase

from taxonomy.models import Job, JobSkills
from test_utils.sample_responses.jobs import JOBS

@mark.django_db
class RefreshJobSkillsCommandTests(TestCase):
    """
    Test command `refresh_job_skills`.
    """
    command = 'refresh_job_skills'

    def setUp(self):
        self.jobs = JOBS
        super(RefreshJobSkillsCommandTests, self).setUp()

    @mock.patch('taxonomy.management.commands.refresh_job_skills.EMSIJobsApiClient.get_jobs')
    def test_job_skills_saved(self, get_job_skills_mock):
        """
        Test that the command creates a Skill and many CourseSkills records.
        """
        get_job_skills_mock.return_value = self.jobs
        jobs = Job.objects.all()
        job_skills = JobSkills.objects.all()
        self.assertEqual(jobs.count(), 0)
        self.assertEqual(job_skills.count(), 0)

        call_command(self.command, 'CERTIFICATIONS', 'CERTIFICATIONS_NAME')

        self.assertEqual(jobs.count(), 2)
        self.assertEqual(job_skills.count(), 4)
