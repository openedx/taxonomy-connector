"""
Management command for fetching and populating skill details, specifically skill category and subcategory.
"""

import logging
import time

from edx_django_utils.db import chunked_queryset

from django.db.models import Q
from django.core.management.base import BaseCommand, CommandError

from taxonomy.emsi.client import EMSISkillsApiClient
from taxonomy.emsi.parsers.skill_parsers import SkillDataParser
from taxonomy.exceptions import TaxonomyAPIError
from taxonomy.models import Skill, SkillCategory, SkillSubCategory
from taxonomy.constants import EMSI_API_RATE_LIMIT_PER_SEC


LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Management command for fetching and populating skill details, specifically skill category and subcategory.

    Example usage:
        $ # Fetch skill category and subcategory for all the skills in the system.
        $ ./manage.py fetch_skill_details
        """
    help = 'Fetch and populate skill category and subcategory.'

    def _update_skill_category_and_sub_category(self, skill, skill_data):
        """
        Persist the skill category and subcategory data in the database.

        Arguments:
            skill (Skill): Skill instance whose category and subcategory needs to be added/updated.
            skill_data (dict): A dictionary containing skill category and subcategory.
        """
        LOGGER.info('Updating category and subcategory data for skill external id {}.'.format(skill.external_id))
        category = skill_data.get('category')
        subcategory = skill_data.get('subcategory')
        if category:
            skill_category, _ = SkillCategory.objects.get_or_create(
                id=category['id'],
                defaults={'name': category['name']}
            )
            skill.category = skill_category

            if subcategory:
                skill_subcategory, _ = SkillSubCategory.objects.get_or_create(
                    id=subcategory['id'],
                    defaults={'name': subcategory['name']},
                    category=skill_category,
                )
                skill.subcategory = skill_subcategory

            skill.save()

    def _fetch_skill_category_and_sub_category(self):
        """
        Fetch skill category and subcategory data from EMSI and update the database accordingly.
        """
        client = EMSISkillsApiClient()
        try:
            skills = Skill.objects.filter(Q(category__isnull=True) | Q(subcategory__isnull=True))
            for chunked_skills in chunked_queryset(skills, chunk_size=100):
                for index, skill in enumerate(chunked_skills, start=1):
                    # EMSI only allows 5 requests/sec
                    # We need to add one sec delay after every 5 requests to prevent 429 errors
                    if index % EMSI_API_RATE_LIMIT_PER_SEC == 0:
                        time.sleep(1)  # sleep for 1 second

                    response = client.get_skill_details(skill_id=skill.external_id)
                    skill_data_parser = SkillDataParser(response=response)
                    self._update_skill_category_and_sub_category(
                        skill=skill,
                        skill_data=skill_data_parser.get_skill_category_data()
                    )
        except TaxonomyAPIError as error:
            message = 'Taxonomy API Error for refreshing the skill category and subcategory data for skill. ' \
                      'Error: {}'.format(error)
            LOGGER.error(message)
            raise CommandError(message)
        except KeyError as error:
            message = f'Missing keys in update skill category data. Error: {error}'
            LOGGER.error(message)
            raise CommandError(message)

    def handle(self, *args, **options):
        """
        Entry point for management command execution.
        """
        LOGGER.info('Fetching skill category and subcategory data.')
        self._fetch_skill_category_and_sub_category()
        LOGGER.info('skill category and subcategory data updated successfully.')
