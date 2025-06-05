"""
Tests for chat completion client.
"""
import requests
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
        Test that the chat completion client works as expected when an object is returned.
        """
        chat_prompt = 'how many courses are offered by edx in the data science area'
        expected_chat_response = [{
            "role": "assistant",
            "content": "edx offers 500 courses in the data science area"
        }]
        responses.add(
            method=responses.POST,
            url=settings.XPERT_AI_API_V2,
            json=expected_chat_response,
            status=200,
        )
        chat_response = chat_completion(chat_prompt, 'test system prompt')
        self.assertEqual(chat_response, expected_chat_response[0]['content'])

    @responses.activate
    def test_client_with_errored_response(self):
        """
        Test that the chat completion client works as expected when an api failure occurs.
        """
        chat_prompt = 'how many courses are offered by edx in the data science area'
        expected_chat_response = [{
            "role": "assistant",
            "content": "edx offers 500 courses in the data science area"
        }]
        responses.add(
            method=responses.POST,
            url=settings.XPERT_AI_API_V2,
            json=expected_chat_response,
            status=500,
        )
        with self.assertRaises(requests.exceptions.RequestException):
            chat_completion(chat_prompt, 'test system prompt')

    @responses.activate
    def test_client_with_response_keyerror(self):
        """
        Test the keyerror response flow for chat completion client.
        """
        chat_prompt = 'how many courses are offered by edx in the data science area'
        expected_chat_response = [{
            "role": "assistant",
            "missing_key": "edx offers 500 courses in the data science area"
        }]
        responses.add(
            method=responses.POST,
            url=settings.XPERT_AI_API_V2,
            json=expected_chat_response,
            status=200,
        )
        with self.assertRaises(KeyError):
            chat_completion(chat_prompt, 'test system prompt')

    @responses.activate
    def test_client_with_response_valuerror(self):
        """
        Test the valueerror response flow for chat completion client.
        """
        chat_prompt = 'how many courses are offered by edx in the data science area'
        responses.add(
            method=responses.POST,
            url=settings.XPERT_AI_API_V2,
            body="not a valid json response",
            status=200,
            content_type='application/json'
        )
        with self.assertRaises(ValueError):
            chat_completion(chat_prompt, 'test system prompt')

    @responses.activate
    def test_client_with_response_typeerror(self):
        """
        Test the typeerror response flow for chat completion client.
        """
        chat_prompt = 'how many courses are offered by edx in the data science area'
        expected_chat_response = "not a subsciptable response"
        responses.add(
            method=responses.POST,
            url=settings.XPERT_AI_API_V2,
            json=expected_chat_response,
            status=200,
        )
        with self.assertRaises(TypeError):
            chat_completion(chat_prompt, 'test system prompt')

    @responses.activate
    def test_client_with_response_indexerror(self):
        """
        Test the indexerror response flow for chat completion client.
        """
        chat_prompt = 'how many courses are offered by edx in the data science area'
        expected_chat_response = []
        responses.add(
            method=responses.POST,
            url=settings.XPERT_AI_API_V2,
            json=expected_chat_response,
            status=200,
        )
        with self.assertRaises(IndexError):
            chat_completion(chat_prompt, 'test system prompt')
