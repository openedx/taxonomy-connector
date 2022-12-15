# -*- coding: utf-8 -*-
"""
Tests for the taxonomy API views.
"""
import json
from random import randint

from pytest import mark

from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.test import Client, TestCase
from django.urls import reverse

from taxonomy.models import JobSkills, Skill, SkillCategory
from test_utils.factories import (
    CourseSkillsFactory,
    JobFactory,
    JobPostingsFactory,
    JobSkillFactory,
    SkillCategoryFactory,
    SkillFactory,
    SkillsQuizFactory,
    SkillSubCategoryFactory,
    XBlockSkillDataFactory,
    XBlockSkillsFactory,
)

User = get_user_model()  # pylint: disable=invalid-name
USER_PASSWORD = 'QWERTY'


@mark.django_db
class TestSkillsViewSet(TestCase):
    """
    Tests for ``SkillsViewSet`` view set.
    """

    def setUp(self) -> None:
        super(TestSkillsViewSet, self).setUp()
        self.skills = SkillFactory.simple_generate_batch(True, 3)
        self.xblock_skill_data = XBlockSkillDataFactory.simple_generate_batch(True, 2, skill=self.skills[0])
        self.course_skills = CourseSkillsFactory.simple_generate_batch(True, 2, skill=self.skills[0])
        self.user = User.objects.create(username="rocky")
        self.user.set_password(USER_PASSWORD)
        self.user.save()
        self.client = Client()
        self.client.login(username=self.user.username, password=USER_PASSWORD)
        self.view_url = r'/api/v1/skills/'

    @staticmethod
    def _verify_skill(response_obj, expected_obj):
        """
        Verify that response matches the expected data.
        """
        assert response_obj['id'] == expected_obj.id
        assert response_obj['external_id'] == expected_obj.external_id
        assert response_obj['type_id'] == expected_obj.type_id
        assert response_obj['name'] == expected_obj.name
        assert response_obj['category'] == expected_obj.category.id
        assert response_obj['subcategory'] == expected_obj.subcategory.id

    def _verify_skills_data(self, api_response, expected_data):
        """
        Verify that skills API response matches the expected data.
        """
        response_data = api_response.json()
        assert len(response_data) == len(expected_data)
        for response_obj, expected_obj in zip(response_data, expected_data):
            self._verify_skill(response_obj, expected_obj)

    def test_skills_api(self):
        """
        Verify that skills API returns the expected response.
        """
        api_response = self.client.get(self.view_url)
        self._verify_skills_data(api_response, self.skills)

    def test_skills_api_get_single(self):
        """
        Verify that skills API returns the expected response for given skill id.
        """
        api_response = self.client.get(self.view_url + f"{self.skills[0].id}/")
        response_data = api_response.json()
        self._verify_skill(response_data, self.skills[0])
        assert "courses" in response_data
        assert len(response_data["courses"]) == 2
        assert "xblocks" in response_data
        assert len(response_data["xblocks"]) == 2

    def test_skills_api_filtering(self):
        """
        Verify that skills API filters on the basis of skill names.
        """
        url = f'{self.view_url}?name={self.skills[0].name}'
        api_response = self.client.get(url)
        self._verify_skills_data(api_response, [self.skills[0]])
        url = f'{self.view_url}?name={self.skills[0].name},{self.skills[2].name}'
        api_response = self.client.get(url)
        self._verify_skills_data(api_response, [self.skills[0], self.skills[2]])


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


@mark.django_db
class TestJobTopSkillCategoriesAPIView(TestCase):
    """
    Tests for `JobTopSkillCategoriesAPIView` API view.
    """

    def setUp(self) -> None:
        """
        Setup env.
        """
        super(TestJobTopSkillCategoriesAPIView, self).setUp()
        self.user = User.objects.create(username="rocky", is_staff=True)
        self.user.set_password(USER_PASSWORD)
        self.user.save()
        self.client = Client()
        self.client.login(username=self.user.username, password=USER_PASSWORD)
        self.job = JobFactory()

        self.view_url = reverse('job_top_subcategories', kwargs={"job_id": self.job.id})

    def test_non_staff(self):
        """
        Test that non-staff user should not access this API.
        """
        user = User.objects.create(username="non-staff-rocky", is_staff=False)
        user.set_password(USER_PASSWORD)
        user.save()
        client = Client()
        client.login(username=user.username, password=USER_PASSWORD)
        api_response = client.get(self.view_url)
        assert api_response.status_code == 403

    @staticmethod
    def _create_job_skills_and_skill_category(job, sub_category_count, skills_count):
        """
        Utility to create date required for the API.
        """
        category = SkillCategoryFactory()
        sub_category_batch = SkillSubCategoryFactory.create_batch(sub_category_count, category=category)
        for __ in range(skills_count):
            sub_category_index = randint(0, sub_category_count - 1)
            skill = SkillFactory(category=category, subcategory=sub_category_batch[sub_category_index])
            if randint(0, 1):
                JobSkillFactory(skill=skill, job=job)

    @staticmethod
    def _get_skill_category_stats(category_id, job):
        """
        Get stats of existing records for given Skill category and Job.
        """
        category = SkillCategory.objects.get(id=category_id)
        return JobSkills.objects.filter(
            job=job, skill__in=category.skill_set.all()
        ).aggregate(
            total_significance=Sum('significance'),
            total_unique_postings=Sum('unique_postings'),
            total_skills=Count('skill'),
        )

    @staticmethod
    def _assert_skill_category_data(category_data, job):
        """
        Asserts response from the API is correct.
        """
        category = SkillCategory.objects.get(id=category_data['id'])
        job_skills = JobSkills.objects.filter(job=job, skill__in=category.skill_set.all())

        # assert skills inside the skills category
        response_skills = [skill['id'] for skill in category_data['skills']]
        expected_skills = list(job_skills.values_list('skill_id', flat=True))
        assert len(response_skills) == len(expected_skills)
        assert sorted(response_skills) == sorted(expected_skills)

        # assert sub-categories
        response_subcategories = [subcategory['id'] for subcategory in category_data['skills_subcategories']]
        expected_subcategories_ids = list(set(job_skills.values_list('skill__subcategory_id', flat=True).distinct()))
        assert len(response_subcategories) == len(expected_subcategories_ids)
        assert sorted(response_subcategories) == sorted(expected_subcategories_ids)

        # assert 'skills_subcategories' skills, these skills should not just job specific instead all sub-cat skills
        for sub_category in category_data['skills_subcategories']:
            expected_skills = list(Skill.objects.filter(subcategory_id=sub_category['id']).values_list('id', flat=True))
            response_skills = [skill['id'] for skill in sub_category['skills']]
            assert len(response_skills) == len(expected_skills)
            assert sorted(response_skills) == sorted(expected_skills)

    def test_success(self):
        """
        Test success response for the API.
        """
        # creating data for self.job
        for __ in range(10):
            self._create_job_skills_and_skill_category(
                self.job,
                sub_category_count=randint(3, 5),
                skills_count=randint(30, 50)
            )

        # creating more data for other random jobs
        for __ in range(5):
            self._create_job_skills_and_skill_category(
                JobFactory(),
                sub_category_count=randint(2, 3),
                skills_count=randint(10, 15)
            )

        with self.assertNumQueries(7):
            api_response = self.client.get(self.view_url)

        assert api_response.status_code == 200
        data = api_response.json()

        # assert that we are getting top 5 skill categories related to job. make sure there ordering is also correct.
        last_category_stats = None
        for index in range(5):
            this_stats = self._get_skill_category_stats(data['skill_categories'][index]['id'], self.job)
            if last_category_stats is None:
                last_category_stats = this_stats
                continue
            assert (this_stats['total_significance'] < last_category_stats['total_significance']) \
                   or (this_stats['total_significance'] == last_category_stats['total_significance']
                       and this_stats['total_unique_postings'] < last_category_stats['total_unique_postings']) \
                   or (this_stats['total_unique_postings'] == last_category_stats['total_unique_postings']
                       and this_stats['total_skills'] <= last_category_stats['total_skills'])

        # assert every category data individually
        for index in range(5):
            self._assert_skill_category_data(data['skill_categories'][index], self.job)


@mark.django_db
class TestJobHolderUsernamesAPIView(TestCase):
    """
    Tests for `JobHolderUsernamesAPIView` API view.
    """

    def setUp(self) -> None:
        """
        Setup env.
        """
        super(TestJobHolderUsernamesAPIView, self).setUp()
        self.user = User.objects.create(username="rocky", is_staff=True)
        self.user.set_password(USER_PASSWORD)
        self.user.save()
        self.client = Client()
        self.client.login(username=self.user.username, password=USER_PASSWORD)
        self.job = JobFactory()

        self.view_url = reverse('job_holder_usernames', kwargs={"job_id": self.job.id})

    def test_non_staff_user_failure(self):
        """
        Test that non-staff user should not access this API.
        """
        user = User.objects.create(username="non-staff-rocky", is_staff=False)
        user.set_password(USER_PASSWORD)
        user.save()
        client = Client()
        client.login(username=user.username, password=USER_PASSWORD)
        api_response = client.get(self.view_url)
        assert api_response.status_code == 403

    def test_success(self):
        """
        Test success response for the API.
        """
        for __ in range(200):
            SkillsQuizFactory(current_job=self.job)

        with self.assertNumQueries(4):
            api_response = self.client.get(self.view_url)

        # assert that we get status code 200
        assert api_response.status_code == 200
        data = api_response.json()

        # assert that usernames list has size of 100
        assert len(data['usernames']) == 100

        # assert that all usernames are unique in usernames list
        assert len(data['usernames']) == len(set(data['usernames']))


@mark.django_db
class TestXBlockSkillsViewSet(TestCase):
    """
    Tests for ``XBlockSkillsViewSet`` view set.
    """

    def setUp(self) -> None:
        super(TestXBlockSkillsViewSet, self).setUp()
        self.skills = SkillFactory.simple_generate_batch(True, 5)
        self.xblock_skills = XBlockSkillsFactory.simple_generate_batch(True, 3)
        self.xblock_skill_data_objs = XBlockSkillDataFactory.simple_generate_batch(
            False,
            2,
            verified=True,
            xblock=self.xblock_skills[0],
        )
        self.xblock_skill_data_objs.extend(XBlockSkillDataFactory.simple_generate_batch(
            False,
            3,
            verified=False,
            xblock=self.xblock_skills[0],
        ))
        XBlockSkillDataFactory.simple_generate_batch(False, 5, xblock=self.xblock_skills[1])
        for i, xblock_skill_data in enumerate(self.xblock_skill_data_objs):
            xblock_skill_data.skill = self.skills[i]
            xblock_skill_data.save()
        self.user = User.objects.create(username="rocky")
        self.user.set_password(USER_PASSWORD)
        self.user.save()
        self.client = Client()
        self.client.login(username=self.user.username, password=USER_PASSWORD)
        self.view_url = r'/api/v1/xblocks/'

    @staticmethod
    def _verify_xblock(response_obj, expected_obj, verified=None):
        """
        Verify that response matches the expected data.
        """
        assert response_obj['id'] == expected_obj.id
        assert response_obj['usage_key'] == expected_obj.usage_key
        assert response_obj['requires_verification'] == expected_obj.requires_verification
        assert response_obj['auto_processed'] == expected_obj.auto_processed
        skill_count_query = expected_obj.skills
        if verified is not None:
            skill_count_query = skill_count_query.filter(xblockskilldata__verified=verified)
        assert len(response_obj['skills']) == skill_count_query.count()

    def _verify_xblocks_data(self, api_response, expected_data, verified=None):
        """
        Verify that skills API response matches the expected data.
        """
        response_data = api_response.json()
        assert len(response_data) == len(expected_data)
        for response_obj, expected_obj in zip(response_data, expected_data):
            self._verify_xblock(response_obj, expected_obj, verified=verified)

    def test_xblocks_api(self):
        """
        Verify that xblocks API returns the expected response.
        """
        api_response = self.client.get(self.view_url)
        self._verify_xblocks_data(api_response, self.xblock_skills)

    def test_xblocks_api_filtering(self):
        """
        Verify that xblocks API filters on the basis of usage_key and verified flag.
        """
        # filter by single usage_key
        api_response = self.client.get(self.view_url, {"usage_key": self.xblock_skills[0].usage_key})
        self._verify_xblocks_data(api_response, [self.xblock_skills[0]])
        # filter by multiple usage_keys
        api_response = self.client.get(
            self.view_url,
            {"usage_key": f'{self.xblock_skills[0].usage_key},{self.xblock_skills[1].usage_key}'},
        )
        self._verify_xblocks_data(api_response, self.xblock_skills[:2])
        # filter skills by verified = True
        api_response = self.client.get(self.view_url, {"verified": True})
        self._verify_xblocks_data(api_response, self.xblock_skills, verified=True)
        # filter skills by verified = False
        api_response = self.client.get(self.view_url, {"verified": False})
        self._verify_xblocks_data(api_response, self.xblock_skills, verified=False)
        # filter skills by verified = False and xblock by usage_key
        api_response = self.client.get(self.view_url, {
            "verified": False,
            "usage_key": self.xblock_skills[0].usage_key,
        })
        self._verify_xblocks_data(api_response, self.xblock_skills[:1], verified=False)
