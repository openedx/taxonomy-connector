""" Management command for populaing current job of learners in learner profile. """

import logging

from edx_rest_api_client.client import OAuthAPIClient

from django.conf import settings
from django.core.management.base import BaseCommand
from taxonomy.models import SkillsQuiz

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Command for populating current job of learners in extended learner profile.

    This command will populate the current job of learners in their learner profile.
    This profile is the extended profile of the user available in the edx-platform.
    This command will find the current job of the learner based on their recent skill
    quiz attempt and populate it in the learner profile.

    This command is supposed to be run only once in the system.

    Example usage:
        $ # Update the current job of learners.
        $ ./manage.py populate_learner_job
    """

    help = 'Populates current job of learners in extended learner profile.'

    def add_arguments(self, parser):
        parser.add_argument('--oauth-host', required=False,
                            default=settings.BACKEND_SERVICE_EDX_OAUTH2_PROVIDER_URL)
        parser.add_argument('--client-id', required=False,
                            default=settings.BACKEND_SERVICE_EDX_OAUTH2_KEY)
        parser.add_argument('--client-secret', required=False,
                            default=settings.BACKEND_SERVICE_EDX_OAUTH2_SECRET)

    def _get_edx_api_client(self, config):
        return OAuthAPIClient(
            base_url=config['oauth_host'],
            client_id=config['client_id'],
            client_secret=config['client_secret'],
        )

    def _get_recent_distinct_skills_quiz_attempt(self):
        """
        Get the recent skills quiz attempt of learners.

        Returns:
            list: List of recent skills quiz attempt of learners.
        """
        try:
            # Fetch the latest skills quiz attempt of learners.
            skills_quiz_attempts = SkillsQuiz.objects.order_by(
                'username', 'created').values_list(
                'username', 'current_job')

            # Remove the duplicate skills quiz attempts of learners by generating
            # a dictionary of skills quiz attempts with username as key then
            # converting it back to a list of dictionary values.
            learner_and_current_job = list(
                {
                    skills_quiz_attempt[0]: {
                        "username": skills_quiz_attempt[0],
                        "current_job": skills_quiz_attempt[1]
                        }
                    for skills_quiz_attempt in skills_quiz_attempts
                }.values()
            )

            return learner_and_current_job
        except Exception:  # pylint: disable=broad-except
            LOGGER.exception('Error while fetching recent skills quiz attempt.')
            raise

    def _set_current_job_in_learner_profile(self, username, current_job, config):
        """
        Set the current job of learner in their extended profile.

        Args:
            username (string): Learner for which we want to set current job.
            current_job (number): Job of the learner.
        """
        try:
            client = self._get_edx_api_client(config)

            lms_endpoint = 'http://edx.devstack.lms:18000'
            profile_api_endpoint = '/api/user/v1/accounts/{username}/'.format(
                username=username
            )
            url = lms_endpoint + profile_api_endpoint

            response = client.patch(
                url,
                {
                    'extended_profile_fields': {
                        'enterprise_user_current_job': current_job
                    }
                },
                headers={  # Need to use merge-patch+json for partial updates.
                    'Content-Type': 'application/merge-patch+json'
                }
            )
            response.raise_for_status()
        except Exception:  # pylint: disable=bare-except
            LOGGER.exception('Error while setting current job in learner profile.')
            raise

    def _populate_learner_current_job(self, config):
        """
        Populate the current job of learners in extended learner profile.
        """
        skills_quiz_attempts = self._get_recent_distinct_skills_quiz_attempt()
        for skills_quiz_attempt in skills_quiz_attempts:
            username = skills_quiz_attempt['username']
            current_job = skills_quiz_attempt['current_job']
            self._set_current_job_in_learner_profile(username, current_job, config)

    def handle(self, *args, **options):
        """
        Handle the command.

        Args:
            *args: Variable length argument list.
            **options: Arbitrary keyword arguments.
        """
        try:
            LOGGER.info('Populating current job of learners in edx-platform.')
            self._populate_learner_current_job(
                config={
                    'oauth_host': options['oauth_host'],
                    'client_id': options['client_id'],
                    'client_secret': options['client_secret'],
                }
            )
            LOGGER.info('Successfully populated current job of learners.')
        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.exception('Error while populating learner job.')
            raise exc
