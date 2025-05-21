"""
Tests for `generate_job_descriptions` management command.
"""
import mock
from pytest import mark

from django.conf import settings
from django.core.management import call_command
from django.test import TransactionTestCase

from taxonomy.management.commands.generate_job_descriptions import generate_and_store_job_description
from taxonomy.models import Job
from test_utils import factories


def mocked_chat_completion_func(prompt, system_message):  # pylint: disable=unused-argument
    """
    Mocked `chat_completion` to return result based on input arguments.
    """
    return prompt


@mark.django_db
class TestGenerateJobDescriptions(TransactionTestCase):
    """
    Test that `generate_job_descriptions` management command works as expected.
    """
    command = 'generate_job_descriptions'

    @mock.patch('taxonomy.utils.chat_completion', side_effect=mocked_chat_completion_func)
    @mock.patch(
        'taxonomy.management.commands.generate_job_descriptions.generate_and_store_job_description',
        wraps=generate_and_store_job_description
    )  # pylint: disable=invalid-name
    def test_command(self, mocked_generate_and_store_job_description, mocked_chat_completion):
        """
        Test `generate_job_descriptions` management command works correctly.
        """
        # Creating this job to verify later that management command only update jobs with empty descriptions
        existing_job = factories.JobFactory(
            external_id='12345',
            name='first last',
            description='I am description for first.last'
        )

        total_jobs_for_descriptions = 50
        factories.JobFactory.create_batch(total_jobs_for_descriptions)

        call_command(self.command)

        for job in Job.objects.exclude(external_id=existing_job.external_id):
            prompt = settings.JOB_DESCRIPTION_PROMPT.format(job_name=job.name)
            assert job.description == prompt

            assert mocked_generate_and_store_job_description.call_count == total_jobs_for_descriptions
            assert mocked_chat_completion.call_count == total_jobs_for_descriptions
            mocked_generate_and_store_job_description.assert_any_call(job.external_id, job.name)
            mocked_chat_completion.assert_any_call(prompt, mock.ANY)

        job = Job.objects.get(external_id=existing_job.external_id)
        assert job.description == existing_job.description

    @mock.patch('taxonomy.management.commands.generate_job_descriptions.generate_and_store_job_description')  # pylint: disable=invalid-name
    def test_command_with_job_without_name(self, mocked_generate_and_store_job_description):
        """
        Test `generate_job_descriptions` management command works correctly if job has no name.
        """
        Job(external_id='11111').save()
        call_command(self.command)
        mocked_generate_and_store_job_description.assert_not_called()
