# -*- coding: utf-8 -*-
"""
Tests for the taxonomy API views.
"""

import json

from pytest import mark

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from test_utils.factories import JobFactory, SkillFactory

User = get_user_model()  # pylint: disable=invalid-name
USER_PASSWORD = 'QWERTY'


@mark.django_db
class TestSkillsQuizViewSet(TestCase):
    """
    Tests for ``SkillsQuizViewSet`` view set.
    """

    def setUp(self) -> None:
        super(TestSkillsQuizViewSet, self).setUp()
        self.skill_a = SkillFactory()
        self.skill_b = SkillFactory()
        self.job_a = JobFactory()
        self.job_b = JobFactory()
        self.user = User.objects.create(username="rocky")
        self.user.set_password(USER_PASSWORD)
        self.user.save()
        self.client = Client()
        self.client.login(username=self.user.username, password=USER_PASSWORD)
        self.view_url = r'/api/v1/skills-quiz/'

    def test_skills_quiz_api_post(self):
        """
        Test the Post endpoint of API.
        """
        post_data = {
            'goal': 'change_careers',
            'current_job': self.job_a.id,
            'skill_names': [self.skill_a.name, self.skill_b.name],
            'future_jobs': [self.job_a.id, self.job_b.id]
        }
        response = self.client.post(self.view_url, json.dumps(post_data), 'application/json')
        assert response.status_code == 201
        response = response.json()
        assert response['goal'] == post_data['goal']
        assert response['current_job'] == post_data['current_job']
        assert response['username'] == self.user.username
        assert response['skills']
        assert response['skills'] == [self.skill_a.id, self.skill_b.id]
        assert response['future_jobs'] == post_data['future_jobs']
        assert 'skill_names' not in response

    def test_validation_error_for_skill_names(self):
        """
        Test the validation error if wrong skill is sent in the post data.
        """
        unsaved_skill = 'skill not saved'
        post_data = {
            'goal': 'change_careers',
            'current_job': self.job_a.id,
            'skill_names': [self.skill_a.name, unsaved_skill],
            'future_jobs': [self.job_a.id, self.job_b.id]
        }
        response = self.client.post(self.view_url, json.dumps(post_data), 'application/json')
        assert response.status_code == 400
        response = response.json()
        assert 'skill_names' in response
        assert response['skill_names'] == [f"Invalid skill names: ['{unsaved_skill}']"]
