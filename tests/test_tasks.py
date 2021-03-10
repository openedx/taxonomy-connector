"""
Tests for celery tasks.
"""
import logging
import unittest

import mock
from pytest import mark
from testfixtures import LogCapture

from taxonomy.models import CourseSkills, Skill
from taxonomy.tasks import update_course_skills
from test_utils.mocks import MockCourse
from test_utils.providers import DiscoveryCourseMetadataProvider
from test_utils.sample_responses.skills import SKILLS_EMSI_CLIENT_RESPONSE


@mark.django_db
class TaxonomyTasksTests(unittest.TestCase):
    """
    Tests for taxonomy celery tasks.
    """

    def setUp(self):
        self.skills_emsi_client_response = SKILLS_EMSI_CLIENT_RESPONSE
        self.course = MockCourse()
        super().setUp()

    @mock.patch('taxonomy.tasks.get_course_metadata_provider')
    @mock.patch('taxonomy.tasks.utils.EMSISkillsApiClient.get_course_skills')
    def test_update_course_skills_task(self, get_course_skills_mock, get_course_provider_mock):
        """
        Verify that `update_course_skills` task work as expected.
        """
        get_course_skills_mock.return_value = self.skills_emsi_client_response
        get_course_provider_mock.return_value = DiscoveryCourseMetadataProvider([self.course])

        # verify that no `Skill` and `CourseSkills` records exist before executing the task
        skill = Skill.objects.all()
        course_skill = CourseSkills.objects.all()
        self.assertEqual(skill.count(), 0)
        self.assertEqual(course_skill.count(), 0)

        update_course_skills.delay([self.course.uuid])

        self.assertEqual(skill.count(), 4)
        self.assertEqual(course_skill.count(), 4)

    @mock.patch('taxonomy.tasks.get_course_metadata_provider')
    @mock.patch('taxonomy.tasks.utils.EMSISkillsApiClient.get_course_skills')
    def test_update_course_skills_task_with_no_course_found(self, get_course_skills_mock, get_course_provider_mock):
        """
        Verify that `update_course_skills` task work as expected.
        """
        get_course_skills_mock.return_value = self.skills_emsi_client_response
        get_course_provider_mock.return_value = DiscoveryCourseMetadataProvider([])

        # verify that no `Skill` and `CourseSkills` records exist before executing the task
        skill = Skill.objects.all()
        course_skill = CourseSkills.objects.all()
        self.assertEqual(skill.count(), 0)
        self.assertEqual(course_skill.count(), 0)

        with LogCapture(level=logging.INFO) as log_capture:
            update_course_skills.delay([self.course.uuid])
            messages = [record.msg for record in log_capture.records]
            self.assertEqual(
                messages,
                [
                    '[TAXONOMY] refresh_course_skills task triggered',
                    '[TAXONOMY] No course found with uuids [%d] to update skills.',
                    'Task %(name)s[%(id)s] succeeded in %(runtime)ss: %(return_value)s'
                ]
            )

        self.assertEqual(skill.count(), 0)
        self.assertEqual(course_skill.count(), 0)
