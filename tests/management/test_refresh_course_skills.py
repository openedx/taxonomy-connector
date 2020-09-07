# -*- coding: utf-8 -*-
"""
Tests for the django management command `refresh_course_skills`.
"""

import mock
from pytest import mark

from django.core.management import call_command
from django.test import TestCase

from taxonomy.models import CourseSkills, Skill
from test_utils.sample_responses.skills import SKILLS
from test_utils.mocks import MockCourse


@mark.django_db
class RefreshCourseSkillsCommandTests(TestCase):
    """
    Test command `refresh_course_skills`.
    """
    command = 'refresh_course_skills'

    def setUp(self):
        self.skills = SKILLS
        self.course_1 = MockCourse()
        self.course_2 = MockCourse()
        self.course_3 = MockCourse()
        super(RefreshCourseSkillsCommandTests, self).setUp()

    @mock.patch('taxonomy.management.commands.refresh_course_skills.get_courses')
    @mock.patch('taxonomy.management.commands.refresh_course_skills.EMSISkillsApiClient.get_course_skills')
    def test_course_skill_saved(self, get_course_skills_mock, get_courses_mock):
        """
        Test that the command creates a Skill and many CourseSkills records.
        """
        get_course_skills_mock.return_value = self.skills
        get_courses_mock.return_value = [self.course_1, self.course_2]
        skill = Skill.objects.all()
        course_skill = CourseSkills.objects.all()
        self.assertEqual(skill.count(), 0)
        self.assertEqual(course_skill.count(), 0)

        call_command(self.command, '--course', self.course_1.uuid, '--course', self.course_2.uuid, '--commit')

        self.assertEqual(skill.count(), 4)
        self.assertEqual(course_skill.count(), 8)

        call_command(self.command, '--course', self.course_1.uuid, '--course', self.course_2.uuid, '--commit')

        self.assertEqual(skill.count(), 4)
        self.assertEqual(course_skill.count(), 8)

        get_courses_mock.return_value = [self.course_3, self.course_1]
        call_command(self.command, '--course', self.course_3.uuid, '--course', self.course_1.uuid, '--commit')

        self.assertEqual(skill.count(), 4)
        self.assertEqual(course_skill.count(), 12)
