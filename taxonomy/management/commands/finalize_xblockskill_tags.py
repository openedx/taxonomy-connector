# -*- coding: utf-8 -*-
"""
Management command for finalizing the xblockskill tags based on number of votes.
"""

import logging

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.translation import gettext as _

from taxonomy.exceptions import InvalidCommandOptionsError
from taxonomy.models import XBlockSkillData

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Command to check if xblockskill tags are verified based on votes.

    The tags are marked as verified when it's verified count is
    above the minimum votes, and the ratio of verified count to
    the total count is above the ratio threshold. Both the
    minimum votes and ratio threshold values are configurable.
    Example usage:
        $ ./manage.py finalize_xblockskill_tags
    """
    help = 'Checks the votes on xblockskill tags to verify it'

    def add_arguments(self, parser):
        """
        Add arguments to the command parser
        """
        parser.add_argument(
            '--min-verified-votes',
            help=_('Minimum number of votes required for verification'),
        )
        parser.add_argument(
            '--ratio-verified-threshold',
            help=_('Ratio of min verified_count to total count for verification'),
        )
        parser.add_argument(
            '--min-ignored-votes',
            help=_('Minimum number of times the skill must be ignored to be blacklisted'),
        )
        parser.add_argument(
            '--ratio-ignored-threshold',
            help=_('Ratio of min ignored_count to total count for blacklisting'),
        )

    @staticmethod
    def _get_and_validate_argument_value(argument, setting_key, options):
        """
        Gets argument value from arguments or settings. Raises error if None.
        """
        value = options.get(argument, None) or getattr(settings, setting_key, None)
        if value is None:
            raise InvalidCommandOptionsError(
                f'Either configure {setting_key} in settings or pass with arg --{argument.replace("_", "-")}'
            )
        return value

    @staticmethod
    def _is_over_threshold(actual_count, total_count, min_votes, ratio_threshold):
        """
        Checks if count passes min count and ratio test.
        """
        has_min_votes = bool(actual_count > int(min_votes))
        count_ratio = float(actual_count / total_count)
        crosses_ratio_threshold = bool(count_ratio > float(ratio_threshold))
        return has_min_votes and crosses_ratio_threshold

    def handle(self, *args, **options):
        """
        Entry point for management command execution.
        """
        LOGGER.info('Starting xblockskill tags verification task')

        min_verified_votes = self._get_and_validate_argument_value(
            'min_verified_votes',
            "SKILLS_VERIFICATION_THRESHOLD",
            options,
        )
        ratio_verified_threshold = self._get_and_validate_argument_value(
            'ratio_verified_threshold',
            "SKILLS_VERIFICATION_RATIO_THRESHOLD",
            options,
        )
        min_ignored_votes = self._get_and_validate_argument_value(
            'min_ignored_votes',
            "SKILLS_IGNORED_THRESHOLD",
            options,
        )
        ratio_ignored_threshold = self._get_and_validate_argument_value(
            'ratio_ignored_threshold',
            "SKILLS_IGNORED_RATIO_THRESHOLD",
            options,
        )

        with transaction.atomic():
            unverified_skills = XBlockSkillData.objects.filter(verified=False, is_blacklisted=False)
            for xblock_skill in unverified_skills:
                verified_count = xblock_skill.verified_count if xblock_skill.verified_count else 0
                ignored_count = xblock_skill.ignored_count if xblock_skill.ignored_count else 0
                total_count = int(verified_count + ignored_count)
                if total_count <= 0:
                    continue
                if self._is_over_threshold(verified_count, total_count, min_verified_votes, ratio_verified_threshold):
                    xblock_skill.verified = True
                    xblock_skill.save()
                    LOGGER.info(
                        '[%s] skill tag for the xblock [%s] has been verified',
                        xblock_skill.skill.name,
                        xblock_skill.xblock.usage_key
                    )
                elif self._is_over_threshold(ignored_count, total_count, min_ignored_votes, ratio_ignored_threshold):
                    xblock_skill.is_blacklisted = True
                    xblock_skill.save()
                    LOGGER.info(
                        '[%s] skill tag for the xblock [%s] has been blacklisted',
                        xblock_skill.skill.name,
                        xblock_skill.xblock.usage_key
                    )
        LOGGER.info('Xblockskill tags verification task is completed')
