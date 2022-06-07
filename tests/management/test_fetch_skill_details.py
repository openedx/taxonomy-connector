# -*- coding: utf-8 -*-
"""
Tests for the django management command `fetch_skill_details`.
"""
import responses
from pytest import mark, raises
from faker import Faker

from django.core.management import call_command
from django.core.management.base import CommandError

from test_utils import factories
from test_utils.testcase import TaxonomyTestCase

from taxonomy.models import Skill, SkillCategory, SkillSubCategory
from taxonomy.emsi.client import EMSISkillsApiClient
from taxonomy.emsi.parsers.skill_parsers import INVALID_NAMES


FAKER = Faker()

INVALID_NAMES = list(INVALID_NAMES)


@mark.django_db
class RefreshCourseSkillsCommandTests(TaxonomyTestCase):
    """
    Test command `fetch_skill_details`.
    """
    command = 'fetch_skill_details'

    def setUp(self):
        super().setUp()

        self.mock_access_token()

    @responses.activate
    def test_skill_category_and_subcategory_saved(self):
        """
        Test that the command adds skill category and subcategory.
        """
        skills_already_having_category = set(factories.SkillFactory.create_batch(5))
        skills = set(factories.SkillFactory.create_batch(20, category=None, subcategory=None))

        # this set is supposed to have category returned by the API.
        skills_set_1 = set(FAKER.random_elements(elements=skills, length=10, unique=True))

        # this set is supposed to not have category returned by the API.
        skills_set_2 = skills.difference(skills_set_1)

        for skill in skills_set_1:
            get_skill_details = {
                'data': {
                    'category': {'id': FAKER.random_int(), 'name': FAKER.word()},
                    'subcategory': {'id': FAKER.random_int(), 'name': FAKER.word()},
                }
            }
            responses.add(
                method=responses.GET,
                url=EMSISkillsApiClient.API_BASE_URL + f'/skills/{skill.external_id}',
                json=get_skill_details,
            )

        for skill in skills_set_2:
            if FAKER.pybool():
                get_skill_details = {
                    'data': {
                        'category': {
                            'id': FAKER.random_int(), 'name': FAKER.random.choice(INVALID_NAMES)
                        },
                        'subcategory': {
                            'id': FAKER.random_int(), 'name': FAKER.random.choice(INVALID_NAMES)
                        },
                    }
                }
            else:
                get_skill_details = {
                    'data': {
                        'category': None,
                        'subcategory': None,
                    }
                }
            responses.add(
                method=responses.GET,
                url=EMSISkillsApiClient.API_BASE_URL + f'/skills/{skill.external_id}',
                json=get_skill_details,
            )

        call_command(self.command)

        skills_with_category = Skill.objects.filter(
            category__isnull=False, subcategory__isnull=False
        )
        skills_without_category = Skill.objects.filter(
            category__isnull=True, subcategory__isnull=True
        )

        expected_skills_with_category = skills_already_having_category.union(skills_set_1)

        assert set(skills_with_category) == expected_skills_with_category
        assert set(skills_without_category) == skills_set_2

    @responses.activate
    def test_skill_category_and_subcategory_not_saved_upon_error(self):
        """
        Test that the command handles exceptions while adding skill category and subcategory.
        """
        skill = factories.SkillFactory.create(category=None, subcategory=None)

        get_skill_details = {
            'data': {
                'category': {'id': FAKER.random_int(), 'name': FAKER.word()},
                'subcategory': {'id': FAKER.random_int(), 'name': FAKER.word()},
            }
        }
        responses.add(
            method=responses.GET,
            url=EMSISkillsApiClient.API_BASE_URL + f'/skills/{skill.external_id}',
            json=get_skill_details,
            status=400,
        )

        with raises(
                CommandError,
                match='Taxonomy API Error for refreshing the skill category and subcategory data for skill.'
        ):
            call_command(self.command)

    @responses.activate
    def test_skill_category_and_subcategory_not_saved_upon_error_2(self):
        """
        Test that the command handles invalid responses from API while adding skill category and subcategory.
        """
        skills = factories.SkillFactory.create_batch(2, category=None, subcategory=None)

        for i, skill in enumerate(skills):
            if i % 2 == 0:
                get_skill_details = {
                    'data': {
                        'category': {'id': FAKER.random_int()},  # missing name
                        'subcategory': {'id': FAKER.random_int(), 'name': FAKER.word()},
                    }
                }
            else:
                get_skill_details = {
                    'data': {
                        'category': {'id': FAKER.random_int(), 'name': FAKER.word()},
                        'subcategory': {'name': FAKER.word()},  # missing id
                    }
                }
            responses.add(
                method=responses.GET,
                url=EMSISkillsApiClient.API_BASE_URL + f'/skills/{skill.external_id}',
                json=get_skill_details,
            )

        with raises(
                CommandError,
                match='Missing keys in update skill category data.'
        ):
            call_command(self.command)

    @responses.activate
    def test_skill_category_and_subcategory_not_saved_upon_missing_category(self):
        """
        Test that the command handles invalid responses from API while adding skill category and subcategory.
        """
        skill = factories.SkillFactory.create(category=None, subcategory=None)

        get_skill_details = {
            'data': {
                'category': {},  # Missing category
                'subcategory': {'id': FAKER.random_int(), 'name': FAKER.word()},
            }
        }
        responses.add(
            method=responses.GET,
            url=EMSISkillsApiClient.API_BASE_URL + f'/skills/{skill.external_id}',
            json=get_skill_details,
        )

        # Validate the for missing category both category and subcategory are not saved.
        assert SkillCategory.objects.count() == 0
        assert SkillSubCategory.objects.count() == 0

    @responses.activate
    def test_skill_category_and_subcategory_not_saved_upon_missing_subcategory(self):
        """
        Test that the command handles invalid responses from API while adding skill category and subcategory.
        """
        skill = factories.SkillFactory.create(category=None, subcategory=None)

        get_skill_details = {
            'data': {
                'category': {'id': FAKER.random_int(), 'name': FAKER.word()},
                'subcategory': {},  # Missing subcategory
            }
        }
        responses.add(
            method=responses.GET,
            url=EMSISkillsApiClient.API_BASE_URL + f'/skills/{skill.external_id}',
            json=get_skill_details,
        )

        # Validate the for missing subcategory both category and subcategory are not saved.
        assert SkillCategory.objects.count() == 0
        assert SkillSubCategory.objects.count() == 0

    @responses.activate
    def test_skill_category_and_subcategory_not_saved_upon_missing_category_and_subcategory(self):
        """
        Test that the command handles invalid responses from API while adding skill category and subcategory.
        """
        skill = factories.SkillFactory.create(category=None, subcategory=None)

        get_skill_details = {
            'data': {
                'category': {},  # Missing category
                'subcategory': {},  # Missing subcategory
            }
        }
        responses.add(
            method=responses.GET,
            url=EMSISkillsApiClient.API_BASE_URL + f'/skills/{skill.external_id}',
            json=get_skill_details,
        )

        # Validate the for missing category and subcategory both category and subcategory are not saved.
        assert SkillCategory.objects.count() == 0
        assert SkillSubCategory.objects.count() == 0
