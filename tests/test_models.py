# -*- coding: utf-8 -*-
"""
Tests for the taxonomy models.
"""

from pytest import mark

from django.test import TestCase

from taxonomy.models import Job, JobPostings
from test_utils.factories import BlacklistedCourseSkillFactory


@mark.django_db
class TestJobPostings(TestCase):
    """
    Tests for the ``JobPostings`` model.
    """

    def setUp(self):
        super(TestJobPostings, self).setUp()
        self.job_title = 'Software Engineer'
        self.job = Job.objects.create(name=self.job_title)
        self.median_salary = 6500000
        self.median_posting_duration = 28
        self.unique_postings = 1345
        self.unique_companies = 148
        self.job_posting = JobPostings.objects.create(
            job=self.job,
            median_salary=self.median_salary,
            median_posting_duration=self.median_posting_duration,
            unique_postings=self.unique_postings,
            unique_companies=self.unique_companies
        )

    def test_string_representation(self):
        """
        Test the string representation of the JobPostings model.
        """
        expected_str = '<Job postings for job: {}, have a median_salary: {}, median_posting_duration: {}, ' \
                       'unique_postings: {}, unique hiring companies: {} >'.format(
                           self.job_title, self.median_salary, self.median_posting_duration, self.unique_postings,
                           self.unique_companies)

        expected_repr = '<JobPosting id="{0}" job="{1!r}" median_salary="{2!r}" median_posting_duration="{3!r}" ' \
                        'unique_postings="{4!r} unique_companies={5!r}">'.format(
                            self.job_posting.id, self.job, self.median_salary, self.median_posting_duration,
                            self.unique_postings, self.unique_companies)

        assert expected_str == self.job_posting.__str__()
        assert expected_repr == self.job_posting.__repr__()


@mark.django_db
class TestBlacklistedCourseSkill(TestCase):
    """
    Tests for the `BlacklistedCourseSkill` model.
    """

    def setUp(self):
        super(TestBlacklistedCourseSkill, self).setUp()
        self.black_listed_course_skill = BlacklistedCourseSkillFactory()

    def test_string_representation(self):
        """
        Test the string representation of the BlacklistedCourseSkill model.
        """
        expected_str = '<BlacklistedCourseSkill skill="{}" course_id="{}">'.format(
            self.black_listed_course_skill.skill.name,
            self.black_listed_course_skill.course_id,
        )

        expected_repr = '<BlacklistedCourseSkill id="{0}" skill="{1!r}">'.format(
            self.black_listed_course_skill.id,
            self.black_listed_course_skill.skill,
        )

        assert expected_str == self.black_listed_course_skill.__str__()
        assert expected_repr == self.black_listed_course_skill.__repr__()
