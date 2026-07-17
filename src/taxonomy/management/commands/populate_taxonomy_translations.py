# -*- coding: utf-8 -*-
"""
Management command to populate taxonomy translations using Xpert AI.

This command translates job, skill, and industry data from English to target languages.
It uses source_hash to detect changes and avoid unnecessary retranslations.

Example usage:
    python manage.py populate_taxonomy_translations --language es
    python manage.py populate_taxonomy_translations --language ar --content-type job
    python manage.py populate_taxonomy_translations --language fr --force
"""
import logging

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError, IntegrityError

from taxonomy.models import Industry, Job, Skill, TaxonomyTranslation
from taxonomy.translation_utils import (
    TranslationError,
    get_supported_languages,
    translate_item_with_xpert,
    validate_language_code,
)

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Populate taxonomy translations using Xpert AI.

    This management command translates jobs, skills, and industries from English
    to target languages. It intelligently skips translations that are already
    up-to-date using MD5 hash comparison of source text.
    """

    help = (
        'Populate taxonomy translations using Xpert AI. '
        'Translates jobs, skills, and industries to target languages. '
        'Uses source_hash to skip unchanged content and avoid unnecessary API calls.'
    )

    def add_arguments(self, parser):
        """Add command-line arguments."""
        parser.add_argument(
            '--language',
            type=str,
            required=True,
            help=(
                'Target language code (ISO 639-1). '
                'Supported: {languages}'.format(
                    languages=', '.join(get_supported_languages())
                )
            )
        )

        parser.add_argument(
            '--content-type',
            type=str,
            choices=['job', 'skill', 'industry', 'all'],
            default='all',
            help='Type of content to translate. Default: all'
        )

        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of items to fetch from database in each batch. Default: 100'
        )

        parser.add_argument(
            '--force',
            action='store_true',
            help=(
                'Force retranslation even if source_hash matches. '
                'Useful when translation quality has improved.'
            )
        )

    def handle(self, *args, **options):
        """Execute the command."""

        # Extract options
        language = options['language']
        content_type = options['content_type']
        batch_size = options['batch_size']
        force = options['force']

        # Validate language code
        if not validate_language_code(language):
            raise CommandError(
                'Unsupported language code: {language}. '
                'Supported languages: {supported}'.format(
                    language=language,
                    supported=', '.join(get_supported_languages())
                )
            )

        # Log configuration
        LOGGER.info('=' * 60)
        LOGGER.info('Taxonomy Translation - Xpert AI')
        LOGGER.info('=' * 60)
        LOGGER.info('Configuration:')
        LOGGER.info('  • Target language: %s', language)
        LOGGER.info('  • Content type: %s', content_type)
        LOGGER.info('  • Database batch size: %d', batch_size)
        LOGGER.info('  • Force retranslation: %s', 'Yes' if force else 'No')

        LOGGER.info(
            'Starting taxonomy translation: language=%s, content_type=%s, batch_size=%d, force=%s',
            language, content_type, batch_size, force
        )

        # Initialize statistics
        stats = {'translated': 0, 'skipped': 0, 'errors': 0}

        # Translate each content type
        if content_type in ['job', 'all']:
            job_stats = self.translate_content_type(
                model=Job,
                content_type_name='job',
                language=language,
                batch_size=batch_size,
                force=force
            )
            for key in stats:
                stats[key] += job_stats[key]

        if content_type in ['skill', 'all']:
            skill_stats = self.translate_content_type(
                model=Skill,
                content_type_name='skill',
                language=language,
                batch_size=batch_size,
                force=force
            )
            for key in stats:
                stats[key] += skill_stats[key]

        if content_type in ['industry', 'all']:
            industry_stats = self.translate_content_type(
                model=Industry,
                content_type_name='industry',
                language=language,
                batch_size=batch_size,
                force=force
            )
            for key in stats:
                stats[key] += industry_stats[key]

        # Log summary
        LOGGER.info('=' * 60)
        LOGGER.info('Translation Summary')
        LOGGER.info('=' * 60)
        LOGGER.info('Translated: %d', stats['translated'])
        LOGGER.info('Skipped (unchanged): %d', stats['skipped'])

        if stats['errors'] > 0:
            LOGGER.error('Errors: %d', stats['errors'])
            LOGGER.error('Translation completed with %d errors', stats['errors'])
        else:
            LOGGER.info('Errors: 0')

        total_processed = stats['translated'] + stats['skipped'] + stats['errors']
        LOGGER.info('Total processed: %d', total_processed)

        LOGGER.info(
            'Translation completed: translated=%d, skipped=%d, errors=%d',
            stats['translated'], stats['skipped'], stats['errors']
        )

    def translate_content_type(self, model, content_type_name, language, batch_size, force):
        """
        Translate all entities of a content type to target language.

        This is a generic method that works for Job, Skill, and Industry models.

        Args:
            model: Django model class (Job, Skill, or Industry)
            content_type_name (str): Content type name ('job', 'skill', 'industry')
            language (str): Target language code
            batch_size (int): Number of items to fetch from database per batch
            force (bool): Force retranslation

        Returns:
            dict: Statistics for this content type
        """
        LOGGER.info('Starting translation for content_type=%s', content_type_name)

        # Get queryset - exclude items without required fields
        queryset = model.objects.exclude(name__isnull=True)

        # For jobs and skills, also exclude those without external_id
        if hasattr(model, 'external_id'):
            queryset = queryset.exclude(external_id__isnull=True)

        total = queryset.count()

        if total == 0:
            LOGGER.info('No %ss found to translate', content_type_name)
            return {'translated': 0, 'skipped': 0, 'errors': 0}

        LOGGER.info('Found %d %ss to process', total, content_type_name)

        # Track statistics for this content type
        stats = {'translated': 0, 'skipped': 0, 'errors': 0}

        # Process in batches
        for i in range(0, total, batch_size):
            batch = queryset[i:i + batch_size]
            batch_stats = self.process_batch(
                entities=batch,
                content_type_name=content_type_name,
                language=language,
                force=force
            )

            stats['translated'] += batch_stats['translated']
            stats['skipped'] += batch_stats['skipped']
            stats['errors'] += batch_stats['errors']

            LOGGER.info(
                'Processed %d/%d %ss',
                min(i + batch_size, total),
                total,
                content_type_name
            )

        LOGGER.info(
            'Completed translation for content_type=%s: translated=%d, skipped=%d, errors=%d',
            content_type_name,
            stats['translated'],
            stats['skipped'],
            stats['errors']
        )

        return stats

    def process_batch(self, entities, content_type_name, language, force):
        """
        Process a batch of entities for translation.

        This is a generic method that works for any entity type (Job, Skill, Industry).

        Args:
            entities (QuerySet): Batch of entity objects
            content_type_name (str): Content type name
            language (str): Target language code
            force (bool): Force retranslation

        Returns:
            dict: Batch statistics
        """
        batch_stats = {'translated': 0, 'skipped': 0, 'errors': 0}

        items_to_translate = []

        for entity in entities:
            # - Job/Skill: use external_id
            # - Industry: use code NAICS2 code
            if hasattr(entity, 'external_id'):
                external_id = entity.external_id
            else:
                # Industry: use NAICS2 code
                external_id = str(entity.code)

            # Get description (not available for Industry)
            description = getattr(entity, 'description', '') or ''

            # Calculate source hash
            source_hash = TaxonomyTranslation.calculate_source_hash(
                entity.name,
                description
            )

            # Check if translation needs updating
            should_translate, __ = self._should_translate(
                external_id=external_id,
                content_type=content_type_name,
                language=language,
                source_hash=source_hash,
                force=force
            )

            if not should_translate:
                batch_stats['skipped'] += 1
                continue

            items_to_translate.append({
                'external_id': external_id,
                'title': entity.name,
                'description': description,
                'source_hash': source_hash,
            })

        # Translate items one at a time using Xpert AI
        for idx, item in enumerate(items_to_translate, 1):
            LOGGER.info(
                'Translating %s %d/%d: %s',
                content_type_name,
                idx,
                len(items_to_translate),
                item['external_id']
            )

            try:
                translation = translate_item_with_xpert(
                    title=item['title'],
                    description=item['description'],
                    target_language=language,
                    content_type=content_type_name,
                    external_id=item['external_id']
                )

                # Save translation using update_or_create for atomic operation
                TaxonomyTranslation.objects.update_or_create(
                    external_id=item['external_id'],
                    content_type=content_type_name,
                    language_code=language,
                    defaults={
                        'title': translation.get('title', ''),
                        'description': translation.get('description', ''),
                        'source_hash': item['source_hash'],
                    }
                )

                batch_stats['translated'] += 1
                LOGGER.info(
                    'Saved translation for %s %s to %s',
                    content_type_name,
                    item['external_id'],
                    language
                )

            except TranslationError as error:
                LOGGER.error(
                    'Translation failed for %s %s: %s',
                    content_type_name,
                    item['external_id'],
                    str(error)
                )
                batch_stats['errors'] += 1

            except (IntegrityError, ValidationError, DatabaseError) as error:
                LOGGER.error(
                    'Database error saving translation for %s %s: %s',
                    content_type_name,
                    item['external_id'],
                    str(error),
                    exc_info=True
                )
                batch_stats['errors'] += 1

        return batch_stats

    def _should_translate(self, external_id, content_type, language, source_hash, force):
        """
        Determine if an entity needs translation.

        Args:
            external_id (str): External ID of entity
            content_type (str): Content type name
            language (str): Target language code
            source_hash (str): Current source hash
            force (bool): Force retranslation

        Returns:
            tuple: (should_translate: bool, is_update: bool)
        """
        try:
            existing = TaxonomyTranslation.objects.get(
                external_id=external_id,
                content_type=content_type,
                language_code=language
            )

            # Translation exists - check if it needs updating
            if not force and existing.source_hash == source_hash:
                # English hasn't changed, skip
                return (False, False)
            else:
                # English changed or force flag set, need to update
                return (True, True)

        except TaxonomyTranslation.DoesNotExist:
            # New translation needed
            return (True, False)
