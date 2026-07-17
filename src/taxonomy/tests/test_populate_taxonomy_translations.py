# -*- coding: utf-8 -*-
"""
Tests for populate_taxonomy_translations management command.
"""
import unittest
from unittest.mock import patch

import ddt
import pytest

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import DatabaseError

from taxonomy.models import Industry, Job, Skill, TaxonomyTranslation
from taxonomy.translation_utils import TranslationError


@pytest.mark.django_db
@ddt.ddt
class TestPopulateTaxonomyTranslationsCommand(unittest.TestCase):
    """Test the populate_taxonomy_translations management command."""

    @ddt.data('job', 'skill', 'industry')
    def test_translate_content_type_success(self, content_type):
        """Test successful translation for each content type."""
        # Create test data
        if content_type == 'job':
            Job.objects.create(external_id='ET123', name='Software Engineer', description='Develops apps')
        elif content_type == 'skill':
            Skill.objects.create(external_id='ES123', name='Python', description='Programming language')
        else:
            Industry.objects.create(code=54, name='Technology')

        with patch('taxonomy.translation_utils.chat_completion') as mock_chat:
            external_id = 'ET123' if content_type == 'job' else ('ES123' if content_type == 'skill' else '54')
            mock_chat.return_value = f'{{"title": "Translated", "description": "Desc"}}'

            call_command('populate_taxonomy_translations', '--language', 'es', '--content-type', content_type)

        # Verify translation created
        translation = TaxonomyTranslation.objects.get(
            external_id=external_id,
            content_type=content_type,
            language_code='es'
        )
        assert translation.title == 'Translated'
        assert translation.description == 'Desc'

    @pytest.mark.django_db
    def test_skip_unchanged_translations(self):
        """Test that unchanged translations are skipped."""
        job = Job.objects.create(external_id='ET123', name='Engineer', description='Develops')
        source_hash = TaxonomyTranslation.calculate_source_hash(job.name, job.description)

        # Create existing translation
        TaxonomyTranslation.objects.create(
            external_id='ET123',
            content_type='job',
            language_code='es',
            title='Ingeniero',
            description='Desarrolla',
            source_hash=source_hash
        )

        with patch('taxonomy.translation_utils.chat_completion') as mock_chat:
            call_command('populate_taxonomy_translations', '--language', 'es', '--content-type', 'job')

        # API should not be called
        mock_chat.assert_not_called()

    @pytest.mark.django_db
    def test_update_stale_translations(self):
        """Test that stale translations are updated."""
        job = Job.objects.create(external_id='ET123', name='Engineer Updated', description='New desc')

        # Create stale translation with old hash
        TaxonomyTranslation.objects.create(
            external_id='ET123',
            content_type='job',
            language_code='es',
            title='Old Translation',
            description='Old desc',
            source_hash='old_hash_123'
        )

        with patch('taxonomy.translation_utils.chat_completion') as mock_chat:
            mock_chat.return_value = '{"title": "New Translation", "description": "New"}'

            call_command('populate_taxonomy_translations', '--language', 'es', '--content-type', 'job')

        # Translation should be updated
        translation = TaxonomyTranslation.objects.get(external_id='ET123', content_type='job', language_code='es')
        assert translation.title == 'New Translation'
        assert translation.description == 'New'

    @pytest.mark.django_db
    def test_force_retranslation(self):
        """Test --force flag retranslates even unchanged items."""
        job = Job.objects.create(external_id='ET123', name='Engineer', description='Develops')
        source_hash = TaxonomyTranslation.calculate_source_hash(job.name, job.description)

        TaxonomyTranslation.objects.create(
            external_id='ET123',
            content_type='job',
            language_code='es',
            title='Ingeniero',
            description='Desarrolla',
            source_hash=source_hash
        )

        with patch('taxonomy.translation_utils.chat_completion') as mock_chat:
            mock_chat.return_value = '{"title": "Forced Translation", "description": "Forced"}'

            call_command('populate_taxonomy_translations', '--language', 'es', '--content-type', 'job', '--force')

        # Translation should be updated despite same hash
        translation = TaxonomyTranslation.objects.get(external_id='ET123', content_type='job', language_code='es')
        assert translation.title == 'Forced Translation'

    @pytest.mark.django_db
    def test_invalid_language_code(self):
        """Test command rejects invalid language codes."""
        with pytest.raises(CommandError):
            call_command('populate_taxonomy_translations', '--language', 'xyz')

    @pytest.mark.django_db
    def test_no_items_to_translate(self):
        """Test when there are no items to translate."""
        # Don't create any jobs - empty database
        with patch('taxonomy.translation_utils.chat_completion') as mock_chat:
            call_command('populate_taxonomy_translations', '--language', 'es', '--content-type', 'job')

        # API should not be called
        mock_chat.assert_not_called()
        # Should complete without errors
        assert TaxonomyTranslation.objects.count() == 0

    @pytest.mark.django_db
    def test_translation_error_handling(self):
        """
        Test that command handles TranslationError gracefully.

        When translate_item_with_xpert raises TranslationError (e.g., due to missing title),
        the command should catch it, log the error, increment error counter, and continue
        without saving the incomplete translation.
        """
        # Create test job
        Job.objects.create(external_id='ET123', name='Software Engineer', description='Develops apps')

        with patch('taxonomy.translation_utils.chat_completion') as mock_chat:
            # Simulate incomplete translation (missing title) which triggers TranslationError
            mock_chat.return_value = '{"title": "", "description": "Desc"}'

            # Command should complete and handle the error gracefully
            call_command('populate_taxonomy_translations', '--language', 'es', '--content-type', 'job')

        # No translation should be created because TranslationError was caught
        assert TaxonomyTranslation.objects.filter(external_id='ET123').count() == 0

    @pytest.mark.django_db
    def test_multiple_translation_errors(self):
        """
        Test that command handles multiple TranslationErrors gracefully.

        When multiple items fail to translate (each raising TranslationError),
        the command should catch each error, log it, and continue processing
        remaining items without crashing.
        """
        # Create multiple jobs
        Job.objects.create(external_id='ET001', name='Job 1', description='Desc 1')
        Job.objects.create(external_id='ET002', name='Job 2', description='Desc 2')
        Job.objects.create(external_id='ET003', name='Job 3', description='Desc 3')

        with patch('taxonomy.translation_utils.chat_completion') as mock_chat:
            # All translations fail (empty titles trigger TranslationError)
            mock_chat.return_value = '{"title": "", "description": "Desc"}'

            # Command should complete despite all errors being caught
            call_command('populate_taxonomy_translations', '--language', 'es', '--content-type', 'job')

        # No translations should be created since all raised TranslationError
        assert TaxonomyTranslation.objects.count() == 0

    @pytest.mark.django_db
    def test_database_error_handling(self):
        """
        Test that command handles database errors gracefully.

        When a DatabaseError occurs during save (after successful translation),
        the command should catch it, log the error, increment error counter,
        and continue without crashing.
        """
        # Create test job
        Job.objects.create(external_id='ET123', name='Software Engineer', description='Develops apps')

        with patch('taxonomy.translation_utils.chat_completion') as mock_chat:
            mock_chat.return_value = '{"title": "Ingeniero", "description": "Desarrolla"}'

            # Mock update_or_create to raise DatabaseError
            with patch('taxonomy.models.TaxonomyTranslation.objects.update_or_create') as mock_save:
                mock_save.side_effect = DatabaseError('Database connection failed')

                # Command should complete and handle the database error gracefully
                call_command('populate_taxonomy_translations', '--language', 'es', '--content-type', 'job')

        # No translation should be created due to DatabaseError being caught
        assert TaxonomyTranslation.objects.filter(external_id='ET123').count() == 0
