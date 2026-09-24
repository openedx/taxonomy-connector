# -*- coding: utf-8 -*-
"""
Tests for translation utilities.
"""
import unittest
from unittest.mock import patch

import ddt
import pytest

from taxonomy.translation_utils import (
    TranslationError,
    _build_translation_prompt,
    _parse_translation_response,
    get_supported_languages,
    translate_item_with_xpert,
    validate_language_code,
)


@ddt.ddt
class TestTranslationUtils(unittest.TestCase):
    """Test translation utility functions."""

    @ddt.data(
        ('es', True),
        ('en', False),
        ('ar', False),
        ('xyz', False),
    )
    @ddt.unpack
    def test_validate_language_code(self, language_code, expected):
        """Test language code validation - only Spanish supported."""
        assert validate_language_code(language_code) == expected

    def test_get_supported_languages(self):
        """Test getting supported languages returns only Spanish."""
        languages = get_supported_languages()
        assert languages == ['es']

    def test_build_translation_prompt(self):
        """Test building translation prompt for a single item."""
        prompt = _build_translation_prompt(
            title='Software Engineer',
            description='Develops software',
            content_type='job',
            target_language='es'
        )

        assert 'Software Engineer' in prompt
        assert 'Spanish' in prompt
        assert 'Develops software' in prompt

    @ddt.data(
        # Valid complete response
        (
            '{"title": "Ingeniero", "description": "Desarrolla"}',
            {'title': 'Ingeniero', 'description': 'Desarrolla'}
        ),
        # Response with only title (description defaults to empty)
        (
            '{"title": "Ingeniero"}',
            {'title': 'Ingeniero', 'description': ''}
        ),
        # Response with empty description
        (
            '{"title": "Ingeniero", "description": ""}',
            {'title': 'Ingeniero', 'description': ''}
        ),
    )
    @ddt.unpack
    def test_parse_translation_response_success(self, response, expected):
        """Test parsing valid single-item translation responses."""
        result = _parse_translation_response(response)

        assert result['title'] == expected['title']
        assert result['description'] == expected['description']

    def test_parse_translation_response_missing_description(self):
        """Test parsing response with missing description field uses empty string."""
        response = '{"title": "Ingeniero"}'

        result = _parse_translation_response(response)

        assert result['title'] == 'Ingeniero'
        assert result['description'] == ''  # Missing - fallback

    @ddt.data(
        'This is not JSON',
        '{invalid json}',
        'null',
        '[]',  # Array instead of object
        '123',  # Number instead of object
    )
    def test_parse_translation_response_invalid(self, response):
        """Test parsing invalid responses returns empty dict."""
        result = _parse_translation_response(response)

        # Function handles errors gracefully by returning empty dict
        assert result == {'title': '', 'description': ''}

    @patch('taxonomy.translation_utils.chat_completion')
    def test_translate_item_success(self, mock_chat):
        """Test successful single-item translation."""
        mock_chat.return_value = '{"title": "Ingeniero", "description": "Desarrolla"}'

        result = translate_item_with_xpert(
            title='Engineer',
            description='Develops',
            target_language='es',
            content_type='job',
            external_id='ET123'
        )

        assert result['title'] == 'Ingeniero'
        assert result['description'] == 'Desarrolla'
        assert mock_chat.call_count == 1

    @patch('taxonomy.translation_utils.chat_completion')
    def test_translate_item_api_error(self, mock_chat):
        """Test single-item translation raises TranslationError on API errors."""
        mock_chat.side_effect = Exception('API Error')

        with pytest.raises(TranslationError) as exc_info:
            translate_item_with_xpert(
                title='Engineer',
                description='',
                target_language='es',
                content_type='job',
                external_id='ET123'
            )

        assert 'Failed to translate job ET123' in str(exc_info.value)
        assert 'API Error' in str(exc_info.value)

    @patch('taxonomy.translation_utils.chat_completion')
    def test_translate_item_missing_title_translation(self, mock_chat):
        """Test that TranslationError is raised when title is provided but translation is missing."""
        # Mock returns empty title when we provided a non-empty title
        mock_chat.return_value = '{"title": "", "description": "Desarrolla"}'

        with pytest.raises(TranslationError) as exc_info:
            translate_item_with_xpert(
                title='Engineer',  # Non-empty title provided
                description='Develops',
                target_language='es',
                content_type='job',
                external_id='ET123'
            )

        assert 'Translation missing title' in str(exc_info.value)
        assert 'ET123' in str(exc_info.value)

    @patch('taxonomy.translation_utils.chat_completion')
    def test_translate_item_missing_description_translation(self, mock_chat):
        """Test that TranslationError is raised when description is provided but translation is missing."""
        # Mock returns empty description when we provided a non-empty description
        mock_chat.return_value = '{"title": "Ingeniero", "description": ""}'

        with pytest.raises(TranslationError) as exc_info:
            translate_item_with_xpert(
                title='Engineer',
                description='Develops software applications',  # Non-empty description provided
                target_language='es',
                content_type='job',
                external_id='ET123'
            )

        assert 'Translation missing description' in str(exc_info.value)
        assert 'ET123' in str(exc_info.value)

    @patch('taxonomy.translation_utils.chat_completion')
    def test_translate_item_empty_inputs_no_error(self, mock_chat):
        """Test that no error is raised when inputs are empty and translations are empty."""
        # Empty inputs should not trigger validation error
        mock_chat.return_value = '{"title": "", "description": ""}'

        result = translate_item_with_xpert(
            title='',  # Empty title
            description='',  # Empty description
            target_language='es',
            content_type='job',
            external_id='ET123'
        )

        assert result['title'] == ''
        assert result['description'] == ''
        # No exception should be raised

    @patch('taxonomy.translation_utils.chat_completion')
    def test_translate_item_only_title_provided(self, mock_chat):
        """Test translation when only title is provided (description is empty)."""
        # Only title provided, description empty - should work fine
        mock_chat.return_value = '{"title": "Ingeniero", "description": ""}'

        result = translate_item_with_xpert(
            title='Engineer',  # Non-empty title
            description='',  # Empty description
            target_language='es',
            content_type='job',
            external_id='ET123'
        )

        assert result['title'] == 'Ingeniero'
        assert result['description'] == ''
        # No exception should be raised since description was empty in input
