"""
Tests for chat completion client.
"""
import responses

from django.conf import settings

from taxonomy.openai.client import chat_completion
from test_utils.testcase import TaxonomyTestCase


class TestChatCompletionClient(TaxonomyTestCase):
    """
    Validate chat_completion client.
    """
    @responses.activate
    def test_client(self):
        """
        Test that the chat completion client works as expected.
        """
        chat_prompt = 'how many courses are offered by edx in the data science area'
        expected_chat_response = {
            "role": "assistant",
            "content": "edx offers 500 courses in the data science area"
        }
        responses.add(
            method=responses.POST,
            url=settings.CHAT_COMPLETION_API,
            json=expected_chat_response,
        )
        chat_response = chat_completion(chat_prompt)
        self.assertEqual(chat_response, expected_chat_response['content'])
