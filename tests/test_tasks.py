"""
Tests for celery tasks.
"""
import unittest

import mock
from pytest import mark

from taxonomy.models import CourseSkills, Skill
from taxonomy.tasks import update_course_skills
from test_utils.mocks import MockCourse
from test_utils.providers import DiscoveryCourseMetadataProvider
from test_utils.sample_responses.skills import SKILLS


@mark.django_db
class TaxonomyTasksTests(unittest.TestCase):
    """
    Tests for taxonomy celery tasks.
    """

    def setUp(self):
        self.skills = SKILLS
        self.course = MockCourse()
        super().setUp()

    @mock.patch('taxonomy.tasks.utils.get_course_metadata_provider')
    @mock.patch('taxonomy.tasks.utils.EMSISkillsApiClient.get_course_skills')
    def test_update_course_skills_task(self, get_course_skills_mock, get_course_provider_mock):
        """
        Verify that `update_course_skills` task work as expected.
        """
        get_course_skills_mock.return_value = self.skills
        get_course_provider_mock.return_value = DiscoveryCourseMetadataProvider([self.course])

        # verify that no `Skill` and `CourseSkills` records exist before executing the task
        skill = Skill.objects.all()
        course_skill = CourseSkills.objects.all()
        self.assertEqual(skill.count(), 0)
        self.assertEqual(course_skill.count(), 0)

        update_course_skills.delay(self.course.uuid)

        self.assertEqual(skill.count(), 4)
        self.assertEqual(course_skill.count(), 4)
