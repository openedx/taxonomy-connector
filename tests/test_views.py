# -*- coding: utf-8 -*-
"""
Tests for the taxonomy API views.
"""

from pytest import mark

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from test_utils.factories import SkillFactory

User = get_user_model()  # pylint: disable=invalid-name
USER_PASSWORD = 'QWERTY'


@mark.django_db
class TestSkillsViewSet(TestCase):
    """
    Tests for ``SkillsViewSet`` view set.
    """

    def setUp(self) -> None:
        super(TestSkillsViewSet, self).setUp()
        self.skill_a = SkillFactory()
        self.skill_b = SkillFactory()
        self.skill_c = SkillFactory()
        self.user = User.objects.create(username="rocky")
        self.user.set_password(USER_PASSWORD)
        self.user.save()
        self.client = Client()
        self.client.login(username=self.user.username, password=USER_PASSWORD)
        self.view_url = r'/api/v1/skills/'

    def _verify_skills_data(self, api_response, expected_data):
        """
        Verify that skills API response matches the expected data.
        """
        response_data = api_response.json()
        assert len(response_data) == len(expected_data)
        for response_obj, expected_obj in zip(response_data, expected_data):
            assert response_obj['id'] == expected_obj.id
            assert response_obj['external_id'] == expected_obj.external_id
            assert response_obj['type_id'] == expected_obj.type_id
            assert response_obj['name'] == expected_obj.name
            assert response_obj['category'] == expected_obj.category.id
            assert response_obj['subcategory'] == expected_obj.subcategory.id

    def test_skills_api(self):
        """
        Verify that skills API returns the expected response.
        """
        api_response = self.client.get(self.view_url)
        self._verify_skills_data(api_response, [self.skill_a, self.skill_b, self.skill_c])

    def test_skills_api_filtering(self):
        """
        Verify that skills API filters on the basis of skill names.
        """
        url = f'{self.view_url}?name={self.skill_a.name}'
        api_response = self.client.get(url)
        self._verify_skills_data(api_response, [self.skill_a])
        url = f'{self.view_url}?name={self.skill_a.name},{self.skill_c.name}'
        api_response = self.client.get(url)
        self._verify_skills_data(api_response, [self.skill_a, self.skill_c])
