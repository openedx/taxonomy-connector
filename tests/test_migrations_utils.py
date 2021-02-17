"""
Validate that utility functions are working properly.
"""
from pytest import mark

from django.apps import apps

from taxonomy.migrations_utils import delete_all_records
from taxonomy.models import CourseSkills, Job, JobPostings, JobSkills, Skill
from test_utils import factories
from test_utils.testcase import TaxonomyTestCase


@mark.django_db
class TestMigrationUtils(TaxonomyTestCase):
    """
    Validate migrations utility functions.
    """
    def test_delete_all_records(self):
        skill = factories.SkillFactory()
        job = factories.JobFactory()
        factories.CourseSkillsFactory(skill=skill)
        factories.JobSkillFactory(job=job, skill=skill)
        factories.JobPostingsFactory(job=job)

        self.assertEqual(Skill.objects.count(), 1)
        self.assertEqual(Job.objects.count(), 1)
        self.assertEqual(CourseSkills.objects.count(), 1)
        self.assertEqual(JobSkills.objects.count(), 1)
        self.assertEqual(JobPostings.objects.count(), 1)

        delete_all_records(apps, None)

        self.assertEqual(Skill.objects.count(), 0)
        self.assertEqual(Job.objects.count(), 0)
        self.assertEqual(CourseSkills.objects.count(), 0)
        self.assertEqual(JobSkills.objects.count(), 0)
        self.assertEqual(JobPostings.objects.count(), 0)
