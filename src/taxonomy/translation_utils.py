# -*- coding: utf-8 -*-
"""
Utilities for translating taxonomy data using Xpert AI.

This module provides helper functions to translate job, skill, and industry data
from English to other languages using the Xpert AI translation service.
"""
import json
import logging

from taxonomy.openai.client import chat_completion

LOGGER = logging.getLogger(__name__)


class TranslationError(Exception):
    """Exception raised when translation fails or returns incomplete results."""


def translate_item_with_xpert(title, description, target_language, content_type, external_id):
    """
    Translate a single taxonomy item using Xpert AI.

    This function takes a taxonomy item's title and description and translates
    them from English to the target language using Xpert AI.

    Args:
        title (str): English title/name to translate
        description (str): English description to translate
        target_language (str): Target language code (e.g., 'es', 'ar', 'fr')
        content_type (str): Type of content ('job', 'skill', or 'industry')
        external_id (str): External ID for logging purposes

    Returns:
        dict: Dict containing translated content:
            - title (str): Translated title
            - description (str): Translated description

    Example:
        >>> result = translate_item_with_xpert(
        ...     title='Software Engineer',
        ...     description='Develops software applications',
        ...     target_language='es',
        ...     content_type='job',
        ...     external_id='ET123'
        ... )
        >>> result['title']
        'Ingeniero de Software'
    """
    LOGGER.debug(
        'Translating %s %s to %s using Xpert AI',
        content_type,
        external_id,
        target_language
    )

    try:
        # Build translation prompt
        prompt = _build_translation_prompt(
            title=title,
            description=description,
            content_type=content_type,
            target_language=target_language
        )

        system_message = "You are a professional translator specializing in career and education content."

        # API call for single item
        response = chat_completion(
            prompt=prompt,
            system_message=system_message
        )

        translation = _parse_translation_response(response)

        # Validate translation completeness
        # If title was provided, translation must have title
        if title and not translation['title']:
            raise TranslationError(
                f"Translation missing title for {content_type} {external_id}. "
                f"Input title: '{title}'"
            )

        # If description was provided, translation must have description
        if description and not translation['description']:
            raise TranslationError(
                f"Translation missing description for {content_type} {external_id}. "
                f"Input description length: {len(description)} chars"
            )

        LOGGER.debug(
            'Successfully translated %s %s to %s',
            content_type,
            external_id,
            target_language
        )

        return translation

    except TranslationError:
        # Re-raise validation errors so they can be handled by caller
        raise
    except Exception as error:  # pylint: disable=broad-exception-caught
        LOGGER.error(
            'Error translating %s %s: %s',
            content_type,
            external_id,
            str(error),
            exc_info=True
        )
        # Wrap in TranslationError so caller can handle uniformly
        raise TranslationError(
            f"Failed to translate {content_type} {external_id}: {str(error)}"
        ) from error


def _build_translation_prompt(title, description, content_type, target_language):
    """
    Build a translation prompt for a single item.

    Creates a structured prompt that instructs the AI to translate a single taxonomy
    item (job, skill, or industry) from English to the target language.

    Args:
        title (str): Title/name to translate
        description (str): Description to translate
        content_type (str): Type of content ('job', 'skill', 'industry')
        target_language (str): Target language code

    Returns:
        str: Formatted prompt for Xpert AI

    Example:
        >>> prompt = _build_translation_prompt(
        ...     title='Software Engineer',
        ...     description='Develops apps',
        ...     content_type='job',
        ...     target_language='es'
        ... )
        >>> 'Software Engineer' in prompt
        True
    """
    # Map language codes to full language names
    language_names = {
        'es': 'Spanish',
    }
    language_name = language_names.get(target_language, target_language)

    prompt = f"""Translate the following {content_type} from English to {language_name}.

CRITICAL INSTRUCTIONS:
1. Maintain professional tone appropriate for career/education content
2. Preserve technical terms (e.g., "Python", "JavaScript", "SQL", "AWS", "React")
3. If description is empty, return empty string for description
4. Return ONLY a valid JSON object - no explanations, no markdown, just the object
5. The JSON must have exactly two fields: "title" and "description"

Input to translate:
Title: {title}
Description: {description}

Return translation in this EXACT format (JSON object):
{{"title": "TRANSLATED_TITLE", "description": "TRANSLATED_DESCRIPTION"}}
"""

    return prompt


def _parse_translation_response(response):
    """
    Parse translation response for a single item.

    Validates the response contains valid JSON with title and description fields.

    Args:
        response (str): Response from Xpert AI API containing JSON object

    Returns:
        dict: Translated content with:
            - title (str): Translated title (or empty string on error)
            - description (str): Translated description (or empty string on error)

    Example:
        >>> response = '{"title": "Ingeniero de Software", "description": "Desarrolla aplicaciones"}'
        >>> result = _parse_translation_response(response)
        >>> result['title']
        'Ingeniero de Software'
    """
    try:
        # Parse JSON object
        translated = json.loads(response)
    except json.JSONDecodeError as e:
        LOGGER.error('Failed to parse translation response as JSON: %s', str(e))
        LOGGER.debug('Response content: %s', response[:200])
        return {'title': '', 'description': ''}

    # Validate it's a dict
    if not isinstance(translated, dict):
        LOGGER.error('Expected JSON object, got %s', type(translated).__name__)
        return {'title': '', 'description': ''}

    # Extract and validate fields
    title = str(translated.get('title', '')).strip()
    description = str(translated.get('description', '')).strip()

    return {
        'title': title,
        'description': description
    }


def get_supported_languages():
    """
    Get list of supported language codes for translation.

    Currently only Spanish is supported. English is the source language.

    Returns:
        list: List of ISO 639-1 language codes

    Example:
        >>> languages = get_supported_languages()
        >>> 'es' in languages
        True
    """
    return ['es']


def validate_language_code(language_code):
    """
    Validate that a language code is supported.

    Args:
        language_code (str): Language code to validate

    Returns:
        bool: True if language is supported, False otherwise

    Example:
        >>> validate_language_code('es')
        True
        >>> validate_language_code('xyz')
        False
    """
    return language_code in get_supported_languages()
