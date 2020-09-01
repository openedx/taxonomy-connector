# -*- coding: utf-8 -*-
"""
Tests for the djagno management command `refresh_course_skills`.
"""

import mock
from pytest import mark

from django.core.management import call_command
from django.test import TestCase

from taxonomy.models import CourseSkills, Skill


@mark.django_db
class RefreshCourseSkillsCommandTests(TestCase):
    """
    Test command `refresh_course_skills`.
    """
    command = 'refresh_course_skills'

    def setUp(self):
        self.skills = {
            'data': [
                {
                    'confidence': 1.0,
                    'skill': {
                        'id': 'KS7G7075XZCWK6F9F51J',
                        'infoUrl': 'https://skills.emsidata.com/skills/KS7G7075XZCWK6F9F51J',
                        'name': 'Drainage Systems',
                        'tags': [
                            {
                                'key': 'wikipediaExtract',
                                'value': 'Drainage system may refer to:Drainage system (geomorphology)'
                            },
                            {
                                'key': 'wikipediaUrl',
                                'value': 'https://en.wikipedia.org/wiki/Drainage_system'
                            }
                        ],
                        'type': {
                            'id': 'ST1',
                            'name': 'Hard Skill'
                        }
                    }
                },
                {
                    'confidence': 1.0,
                    'skill': {
                        'id': 'JS7G7075XZCWK6F9F51K',
                        'infoUrl': 'https://skills.emsidata.com/skills/KS7G7075XZCWK6F9F51J',
                        'name': 'Drainage Systems',
                        'tags': [
                            {
                                'key': 'wikipediaExtract',
                                'value': 'Drainage system may refer to:Drainage system (geomorphology)'
                            },
                            {
                                'key': 'wikipediaUrl',
                                'value': 'https://en.wikipedia.org/wiki/Drainage_system'
                            }
                        ],
                        'type': {
                            'id': 'ST1',
                            'name': 'Hard Skill'
                        }
                    }
                }
            ]
        }
        super(RefreshCourseSkillsCommandTests, self).setUp()

    @mock.patch('taxonomy.management.commands.refresh_course_skills.EMSISkillsApiClient.get_course_skills')
    def test_course_skill_saved(self, client_mock):
        """
        Test that the command creates a Skill and many CourseSkills records.
        """
        client_mock.return_value = self.skills
        skill = Skill.objects.all()
        course_skill = CourseSkills.objects.all()
        self.assertEqual(skill.count(), 0)
        self.assertEqual(course_skill.count(), 0)

        call_command(self.command, '--course-id', 'Test_Course1', '--course-id', 'Test_Course2', '--commit')

        self.assertEqual(skill.count(), 2)
        self.assertEqual(course_skill.count(), 4)

        call_command(self.command, '--course-id', 'Test_Course1', '--course-id', 'Test_Course2', '--commit')

        self.assertEqual(skill.count(), 2)
        self.assertEqual(course_skill.count(), 4)

        call_command(self.command, '--course-id', 'Test_Course3', '--course-id', 'Test_Course1', '--commit')

        self.assertEqual(skill.count(), 2)
        self.assertEqual(course_skill.count(), 6)
