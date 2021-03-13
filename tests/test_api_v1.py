from pytest import mark
from django.urls import reverse

from rest_framework.test import APITestCase
from rest_framework import status
from test_utils import factories


TEST_USERNAME = 'taxonomy_user'
TEST_EMAIL = 'taxonomy_user@example.com'
TEST_PASSWORD = 'password'


@mark.django_db
class TestSkillsView(APITestCase):
    def setUp(self):
        """
        Perform operations common to all tests.
        """
        super().setUp()
        self.user = self.create_user(username=TEST_USERNAME, email=TEST_EMAIL, password=TEST_PASSWORD)

        self.url = reverse('skill_list')

        self.whitelisted_skills = [
            'C Plus Plus', 'Command Line Interface', 'Data Structures', 'Biochemistry',
            'Animations', 'Algorithms', 'Data Science', 'Data Wrangling', 'Databases'
        ]
        self.blacklisted_skills = ['Visual Basic', 'Oracle']

        for skill_name in self.whitelisted_skills:
            skill = factories.SkillFactory(name=skill_name)
            factories.CourseSkillsFactory(skill=skill)

        for skill_name in self.blacklisted_skills:
            skill = factories.SkillFactory(name=skill_name)
            factories.CourseSkillsFactory(skill=skill, is_blacklisted=True)

        self.client.login(username=TEST_USERNAME, password=TEST_PASSWORD)

    def create_user(self, username=TEST_USERNAME, password=TEST_PASSWORD, **kwargs):
        """
        Create a test user and set its password.
        """
        user = factories.UserFactory(username=username, **kwargs)
        user.set_password(password)  # pylint: disable=no-member
        user.save()  # pylint: disable=no-member
        return user

    def test_search(self):
        """
        Verify that skills endppoint return all skills when `search` query param is not given
        """
        response = self.client.get(path=self.url)
        assert response.status_code == status.HTTP_200_OK
        skill_names = [skill['name'] for skill in response.json()]
        assert sorted(skill_names) == sorted(self.whitelisted_skills)

    def test_search_with_query_param(self):
        """
        Verify that skills endppoint return filtered skills according to the `search` query param
        """
        response = self.client.get(path=self.url + '?search=data')
        assert response.status_code == status.HTTP_200_OK
        skill_names = [skill['name'] for skill in response.json()]
        assert skill_names == ['Data Structures', 'Data Science', 'Data Wrangling', 'Databases' ]

    def test_search_with_blacklisted_skill(self):
        """
        Verify that skills endppoint does not return blacklised skills.
        """
        response = self.client.get(path=self.url + '?search=Oracle')
        assert response.status_code == status.HTTP_200_OK
        skill_names = [skill['name'] for skill in response.json()]
        assert skill_names == []
