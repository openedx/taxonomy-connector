"""
Tests for taxonomy signals.
"""
import unittest

import mock
from pytest import mark

from taxonomy.models import CourseSkills, Skill
from taxonomy.signals.signals import UPDATE_COURSE_SKILLS
from test_utils.mocks import MockCourse
from test_utils.providers import DiscoveryCourseMetadataProvider
from test_utils.sample_responses.skills import SKILLS_EMSI_CLIENT_RESPONSE


@mark.django_db
class TaxonomyTasksTests(unittest.TestCase):
    """
    Test class for taxonomy signals.
    """

    def setUp(self):
        self.skills_emsi_client_response = SKILLS_EMSI_CLIENT_RESPONSE
        self.course = MockCourse()
        super().setUp()

    @mock.patch('taxonomy.tasks.get_course_metadata_provider')
    @mock.patch('taxonomy.tasks.utils.EMSISkillsApiClient.get_course_skills')
    def test_update_course_skills_task(self, get_course_skills_mock, get_course_provider_mock):
        """
        Verify that `UPDATE_COURSE_SKILLS` signal work as expected.
        """
        get_course_skills_mock.return_value = self.skills_emsi_client_response
        get_course_provider_mock.return_value = DiscoveryCourseMetadataProvider([self.course])

        # verify that no `Skill` and `CourseSkills` records exist before executing the task
        skill = Skill.objects.all()
        course_skill = CourseSkills.objects.all()
        self.assertEqual(skill.count(), 0)
        self.assertEqual(course_skill.count(), 0)

        UPDATE_COURSE_SKILLS.send(sender=None, course_uuid=self.course.uuid)

        self.assertEqual(skill.count(), 4)
        self.assertEqual(course_skill.count(), 4)
