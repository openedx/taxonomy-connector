# -*- coding: utf-8 -*-
"""
Tests for the taxonomy API views.
"""
import json

from pytest import mark

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from test_utils.factories import JobFactory, JobPostingsFactory, JobSkillFactory, SkillFactory, SkillsQuizFactory

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


@mark.django_db
class TestJobsViewSet(TestCase):
    """
    Tests for ``JobsViewSet`` view set.
    """

    def setUp(self) -> None:
        super(TestJobsViewSet, self).setUp()
        self.job_a = JobFactory()
        self.job_b = JobFactory()
        self.job_skill_a = JobSkillFactory(job=self.job_a)
        self.job_skill_b = JobSkillFactory(job=self.job_b)
        self.job_skill_c = JobSkillFactory(job=self.job_b)
        self.user = User.objects.create(username="rocky")
        self.user.set_password(USER_PASSWORD)
        self.user.save()
        self.client = Client()
        self.client.login(username=self.user.username, password=USER_PASSWORD)
        self.view_url = r'/api/v1/jobs/'

    def test_jobs_api(self):
        """
        Verify that jobs API returns the expected response.
        """
        api_response = self.client.get(self.view_url)
        api_response = api_response.json()
        assert len(api_response) == 2
        job_a_response = api_response[0]
        job_b_response = api_response[1]

        # verify response for job a contains correct data
        assert job_a_response['id'] == self.job_a.id
        assert job_a_response['name'] == self.job_a.name
        assert job_a_response['external_id'] == self.job_a.external_id
        assert len(job_a_response['skills']) == 1
        assert job_a_response['skills'][0]['skill']['id'] == self.job_skill_a.skill.id
        assert job_a_response['skills'][0]['skill']['name'] == self.job_skill_a.skill.name

        # verify response for job b contains correct data
        assert job_b_response['id'] == self.job_b.id
        assert job_b_response['name'] == self.job_b.name
        assert job_b_response['external_id'] == self.job_b.external_id
        assert len(job_b_response['skills']) == 2
        assert job_b_response['skills'][0]['skill']['id'] == self.job_skill_b.skill.id
        assert job_b_response['skills'][0]['skill']['name'] == self.job_skill_b.skill.name
        assert job_b_response['skills'][1]['skill']['id'] == self.job_skill_c.skill.id
        assert job_b_response['skills'][1]['skill']['name'] == self.job_skill_c.skill.name


@mark.django_db
class TestJobPostingsViewSet(TestCase):
    """
    Tests for ``JobPostingsViewSet`` view set.
    """

    def setUp(self) -> None:
        super(TestJobPostingsViewSet, self).setUp()
        self.job = JobFactory()
        self.job_posting = JobPostingsFactory(job=self.job)
        self.user = User.objects.create(username="rocky")
        self.user.set_password(USER_PASSWORD)
        self.user.save()
        self.client = Client()
        self.client.login(username=self.user.username, password=USER_PASSWORD)
        self.view_url = r'/api/v1/jobpostings/'

    def test_job_postings_api(self):
        """
        Verify that job postings API returns the expected response.
        """
        api_response = self.client.get(self.view_url)
        api_response = api_response.json()
        assert len(api_response) == 1
        job_posting_response = api_response[0]

        # verify response for job a contains correct data
        assert job_posting_response['id'] == self.job_posting.id
        assert job_posting_response['median_salary'] == self.job_posting.median_salary
        assert job_posting_response['median_posting_duration'] == self.job_posting.median_posting_duration
        assert job_posting_response['unique_postings'] == self.job_posting.unique_postings
        assert job_posting_response['unique_companies'] == self.job_posting.unique_companies
        assert job_posting_response['job']['id'] == self.job_posting.job.id
        assert job_posting_response['job']['name'] == self.job_posting.job.name


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
        self.skills_quiz_a = SkillsQuizFactory(username=self.user.username)
        self.skills_quiz_b = SkillsQuizFactory(username=self.user.username)
        self.skills_quiz_c = SkillsQuizFactory()
        self.client = Client()
        self.client.login(username=self.user.username, password=USER_PASSWORD)
        self.view_url = r'/api/v1/skills-quiz/'

    def _verify_skills_quiz_data(self, api_response, expected_data):
        """
        Verify that skills quiz API response matches the expected data.
        """
        response_data = api_response.json()
        assert len(response_data) == len(expected_data)
        for response_obj, expected_obj in zip(response_data, expected_data):
            assert response_obj['id'] == expected_obj.id
            assert response_obj['goal'] == expected_obj.goal
            assert response_obj['current_job'] == expected_obj.current_job.id
            assert response_obj['future_jobs'] == list(expected_obj.future_jobs.values_list('id', flat=True))

    def test_skills_quiz_api_get(self):
        """
        Verify that skills quiz API returns the expected response.
        """
        api_response = self.client.get(self.view_url)
        self._verify_skills_quiz_data(api_response, [self.skills_quiz_a, self.skills_quiz_b])

    def test_skills_quiz_api_get_for_staff_user(self):
        """
        Verify that skills quiz API returns all quiz for staff user.
        """
        user = User.objects.create(username="rocky-staff", is_staff=True)
        user.set_password(USER_PASSWORD)
        user.save()
        client = Client()
        client.login(username=user.username, password=USER_PASSWORD)
        api_response = client.get(self.view_url)
        self._verify_skills_quiz_data(api_response, [self.skills_quiz_a, self.skills_quiz_b, self.skills_quiz_c])

    def test_skills_quiz_api_post(self):
        """
        Verify skills quiz API post endpoint works correctly.
        """
        post_data = {
            'goal': 'change_careers',
            'current_job': self.job_a.id,
            'skills': [self.skill_a.id, self.skill_b.id],
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
