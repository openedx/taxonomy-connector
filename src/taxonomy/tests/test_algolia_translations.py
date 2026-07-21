# -*- coding: utf-8 -*-
"""
Tests for Algolia translation utilities.
"""
import logging
from collections import deque
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import taxonomy.algolia.utils as algolia_utils
from taxonomy.algolia.utils import (
    build_name_translation_maps,
    create_localized_job_records,
    fetch_jobs_data,
    index_jobs_data_in_algolia,
    translate_industries_array,
    translate_job_record,
    translate_skill_dict,
)
from taxonomy.models import Industry, IndustryJobSkill, Job, JobSkills, Skill, TaxonomyTranslation


@pytest.mark.django_db
class TestBuildNameTranslationMaps:
    """Test building translation maps."""

    @pytest.mark.parametrize('content_type,model_class,external_id,name,translation', [
        ('job', Job, 'ET123', 'Software Engineer', 'Ingeniero de Software'),
        ('skill', Skill, 'ES123', 'Python', 'Python (Programación)'),
        ('industry', Industry, '54', 'Information Technology', 'Tecnología de la Información'),
    ])
    def test_builds_translations(self, content_type, model_class, external_id, name, translation):
        """Test building translations for jobs, skills, and industries."""
        if model_class == Industry:
            model_class.objects.create(code=external_id, name=name)
        else:
            model_class.objects.create(external_id=external_id, name=name)

        TaxonomyTranslation.objects.create(
            external_id=external_id,
            content_type=content_type,
            language_code='es',
            title=translation
        )

        maps = build_name_translation_maps('es')

        assert maps[content_type][name] == translation

    def test_skips_empty_translations(self):
        """Test that empty translations are not included in maps."""
        job = Job.objects.create(external_id='ET123', name='Software Engineer')
        TaxonomyTranslation.objects.create(
            external_id='ET123',
            content_type='job',
            language_code='es',
            title=''  # Empty translation
        )

        maps = build_name_translation_maps('es')

        # Empty translation should not be in the map
        assert 'Software Engineer' not in maps['job']

    def test_returns_empty_maps_when_no_translations(self):
        """Test returns empty dicts when no translations exist."""
        Job.objects.create(external_id='ET123', name='Software Engineer')

        maps = build_name_translation_maps('es')

        assert maps['job'] == {}
        assert maps['skill'] == {}
        assert maps['industry'] == {}

    def test_skips_empty_skill_translation_title(self):
        """Test empty skill translation title is skipped (falls through condition)."""
        Skill.objects.create(external_id='ES123', name='Python')
        TaxonomyTranslation.objects.create(
            external_id='ES123',
            content_type='skill',
            language_code='es',
            title='',
        )

        maps = build_name_translation_maps('es')

        assert 'Python' not in maps['skill']

    def test_accepts_prefetched_translations(self):
        """Test that pre-fetched translations are used without issuing new DB queries."""
        Job.objects.create(external_id='ET123', name='Software Engineer')
        trans = TaxonomyTranslation.objects.create(
            external_id='ET123',
            content_type='job',
            language_code='es',
            title='Ingeniero de Software',
        )

        prefetched = {'job': [trans], 'skill': [], 'industry': []}
        maps = build_name_translation_maps('es', prefetched_translations=prefetched)

        assert maps['job']['Software Engineer'] == 'Ingeniero de Software'


class TestTranslateSkillDict:
    """Test skill dict translation."""

    def test_translates_skill_name(self):
        """Test skill name is translated and all fields are preserved."""
        skill = {
            'name': 'Python',
            'description': 'Programming language',
            'significance': 85,
            'type_id': 'ST1'
        }
        name_maps = {
            'skill': {'Python': 'Python (Lenguaje)'}
        }

        result = translate_skill_dict(skill, name_maps)

        assert result['name'] == 'Python (Lenguaje)'
        assert result['description'] == 'Programming language'
        assert result['significance'] == 85
        assert result['type_id'] == 'ST1'

    def test_fallback_when_translation_missing(self):
        """Test falls back to English when translation not found."""
        skill = {'name': 'JavaScript'}
        name_maps = {'skill': {'Python': 'Python (ES)'}}

        result = translate_skill_dict(skill, name_maps)

        assert result['name'] == 'JavaScript'


class TestTranslateIndustriesArray:
    """Test industries array translation."""

    def test_translates_industry_names(self):
        """Test industry names are translated."""
        industries = [
            {
                'name': 'Information Technology',
                'skills': []
            }
        ]
        name_maps = {
            'industry': {'Information Technology': 'Tecnología de la Información'},
            'skill': {}
        }

        result = translate_industries_array(industries, name_maps)

        assert result[0]['name'] == 'Tecnología de la Información'

    def test_translates_nested_skills(self):
        """Test nested skills are translated."""
        industries = [
            {
                'name': 'IT',
                'skills': ['Python', 'Java', 'Cloud Computing']
            }
        ]
        name_maps = {
            'industry': {'IT': 'TI'},
            'skill': {
                'Python': 'Python (Programación)',
                'Cloud Computing': 'Computación en la Nube'
            }
        }

        result = translate_industries_array(industries, name_maps)

        assert result[0]['name'] == 'TI'
        assert result[0]['skills'][0] == 'Python (Programación)'
        assert result[0]['skills'][1] == 'Java'  # Fallback
        assert result[0]['skills'][2] == 'Computación en la Nube'

    def test_handles_empty_industries(self):
        """Test handles empty industries list."""
        result = translate_industries_array([], {'industry': {}, 'skill': {}})

        assert result == []


@pytest.mark.django_db
class TestTranslateJobRecord:
    """Test job record translation."""

    def test_translates_job_name(self):
        """Test job name is translated."""
        Job.objects.create(external_id='ET123', name='Software Engineer')
        TaxonomyTranslation.objects.create(
            external_id='ET123',
            content_type='job',
            language_code='es',
            title='Ingeniero de Software',
            description='Desarrolla software'
        )

        english_job = {
            'objectID': 'job-ET123',
            'id': 1,
            'external_id': 'ET123',
            'name': 'Software Engineer',
            'description': 'Develops software',
            'skills': [],
            'job_postings': [],
            'industry_names': [],
            'industries': [],
            'similar_jobs': [],
            'b2c_opt_in': True,
            'job_sources': ['course_skill']
        }

        name_maps = {'job': {'Software Engineer': 'Ingeniero de Software'}, 'skill': {}, 'industry': {}}
        desc_maps = {
            'job': {
                'ET123': TaxonomyTranslation.objects.get(external_id='ET123')
            },
            'skill': {},
            'industry': {}
        }

        result = translate_job_record(english_job, name_maps, desc_maps, 'es')

        assert result['objectID'] == 'job-ET123-es'
        assert result['name'] == 'Ingeniero de Software'
        assert result['description'] == 'Desarrolla software'
        assert result['metadata_language'] == 'es'

    def test_translates_all_nested_fields(self):
        """Test all nested arrays are translated."""
        english_job = {
            'objectID': 'job-ET123',
            'id': 1,
            'external_id': 'ET123',
            'name': 'Engineer',
            'description': 'Desc',
            'skills': [
                {'name': 'Python', 'significance': 90}
            ],
            'job_postings': [{'id': 1}],
            'industry_names': ['IT', 'Software'],
            'industries': [
                {'name': 'IT', 'skills': ['Cloud']}
            ],
            'similar_jobs': ['Senior Engineer', 'Architect'],
            'b2c_opt_in': False,
            'job_sources': ['job_skill']
        }

        name_maps = {
            'job': {'Engineer': 'Ingeniero', 'Senior Engineer': 'Ingeniero Senior'},
            'skill': {'Python': 'Python (ES)', 'Cloud': 'Nube'},
            'industry': {'IT': 'TI', 'Software': 'Software'}
        }
        desc_maps = {'job': {}, 'skill': {}, 'industry': {}}

        result = translate_job_record(english_job, name_maps, desc_maps, 'es')

        # Check skills translated
        assert result['skills'][0]['name'] == 'Python (ES)'
        assert result['skills'][0]['significance'] == 90

        # Check industry_names translated
        assert result['industry_names'] == ['TI', 'Software']

        # Check industries with nested skills translated
        assert result['industries'][0]['name'] == 'TI'
        assert result['industries'][0]['skills'] == ['Nube']

        # Check similar_jobs translated
        assert result['similar_jobs'][0] == 'Ingeniero Senior'
        assert result['similar_jobs'][1] == 'Architect'  # Fallback

    def test_preserves_non_translatable_fields(self):
        """Test non-translatable fields are preserved."""
        english_job = {
            'objectID': 'job-ET123',
            'id': 1,
            'external_id': 'ET123',
            'name': 'Engineer',
            'description': '',
            'skills': [],
            'job_postings': [{'id': 1, 'url': 'http://example.com'}],
            'industry_names': [],
            'industries': [],
            'similar_jobs': [],
            'b2c_opt_in': True,
            'job_sources': ['course_skill', 'job_skill']
        }

        name_maps = {'job': {}, 'skill': {}, 'industry': {}}
        desc_maps = {'job': {}, 'skill': {}, 'industry': {}}

        result = translate_job_record(english_job, name_maps, desc_maps, 'es')

        assert result['job_postings'] == [{'id': 1, 'url': 'http://example.com'}]
        assert result['b2c_opt_in'] is True
        assert result['job_sources'] == ['course_skill', 'job_skill']
        assert result['id'] == 1
        # external_id is made composite so Algolia's `distinct` setting does not
        # collapse localized records onto the English record with the same id.
        assert result['external_id'] == 'ET123-es'

    def test_localized_record_has_language_sort_priority_one(self):
        """Test localized records have language_sort_priority=1."""
        english_job = {
            'objectID': 'job-ET123', 'id': 1, 'external_id': 'ET123',
            'name': 'Engineer', 'description': '', 'skills': [],
            'job_postings': [], 'industry_names': [], 'industries': [],
            'similar_jobs': [], 'b2c_opt_in': False, 'job_sources': []
        }
        name_maps = {'job': {}, 'skill': {}, 'industry': {}}
        desc_maps = {'job': {}, 'skill': {}, 'industry': {}}

        result = translate_job_record(english_job, name_maps, desc_maps, 'es')

        assert result['language_sort_priority'] == 1

    def test_fallback_to_english_when_no_description(self):
        """Test falls back to English description when translation empty."""
        english_job = {
            'objectID': 'job-ET123',
            'id': 1,
            'external_id': 'ET123',
            'name': 'Engineer',
            'description': 'English description',
            'skills': [],
            'job_postings': [],
            'industry_names': [],
            'industries': [],
            'similar_jobs': [],
            'b2c_opt_in': False,
            'job_sources': []
        }

        name_maps = {'job': {}, 'skill': {}, 'industry': {}}
        desc_maps = {'job': {}, 'skill': {}, 'industry': {}}

        result = translate_job_record(english_job, name_maps, desc_maps, 'es')

        assert result['description'] == 'English description'

    def test_uses_existing_object_id_format(self):
        """Localized objectID should preserve existing serializer format."""
        english_job = {
            'objectID': 'custom-prefix-ET123',
            'id': 1,
            'external_id': 'ET123',
            'name': 'Engineer',
            'description': '',
            'skills': [],
            'job_postings': [],
            'industry_names': [],
            'industries': [],
            'similar_jobs': [],
            'b2c_opt_in': False,
            'job_sources': []
        }
        name_maps = {'job': {}, 'skill': {}, 'industry': {}}
        desc_maps = {'job': {}, 'skill': {}, 'industry': {}}

        result = translate_job_record(english_job, name_maps, desc_maps, 'es')

        assert result['objectID'] == 'custom-prefix-ET123-es'

    def test_job_postings_list_is_shallow_copied(self):
        """Localized record should not share the same postings list reference."""
        english_postings = [{'id': 1}]
        english_job = {
            'objectID': 'job-ET123',
            'id': 1,
            'external_id': 'ET123',
            'name': 'Engineer',
            'description': '',
            'skills': [],
            'job_postings': english_postings,
            'industry_names': [],
            'industries': [],
            'similar_jobs': [],
            'b2c_opt_in': False,
            'job_sources': []
        }
        name_maps = {'job': {}, 'skill': {}, 'industry': {}}
        desc_maps = {'job': {}, 'skill': {}, 'industry': {}}

        result = translate_job_record(english_job, name_maps, desc_maps, 'es')

        assert result['job_postings'] == english_postings
        assert result['job_postings'] is not english_postings


@pytest.mark.django_db
class TestCreateLocalizedJobRecords:
    """Test creating localized job records."""

    def test_creates_spanish_records(self):
        """Test creates Spanish variant of English jobs."""
        job = Job.objects.create(external_id='ET123', name='Engineer')
        TaxonomyTranslation.objects.create(
            external_id='ET123',
            content_type='job',
            language_code='es',
            title='Ingeniero',
            description='Descripción'
        )

        english_jobs = [{
            'objectID': 'job-ET123',
            'id': 1,
            'external_id': 'ET123',
            'name': 'Engineer',
            'description': 'Description',
            'skills': [],
            'job_postings': [],
            'industry_names': [],
            'industries': [],
            'similar_jobs': [],
            'b2c_opt_in': False,
            'job_sources': []
        }]

        spanish_jobs = create_localized_job_records(english_jobs, 'es')

        assert len(spanish_jobs) == 1
        assert spanish_jobs[0]['objectID'] == 'job-ET123-es'
        assert spanish_jobs[0]['external_id'] == 'ET123-es'
        assert spanish_jobs[0]['name'] == 'Ingeniero'
        assert spanish_jobs[0]['description'] == 'Descripción'
        assert spanish_jobs[0]['metadata_language'] == 'es'
        assert spanish_jobs[0]['language_sort_priority'] == 1

    def test_creates_multiple_records(self):
        """Test creates translations for multiple jobs."""
        Job.objects.create(external_id='ET1', name='Engineer')
        Job.objects.create(external_id='ET2', name='Designer')

        TaxonomyTranslation.objects.create(
            external_id='ET1', content_type='job', language_code='es', title='Ingeniero'
        )
        TaxonomyTranslation.objects.create(
            external_id='ET2', content_type='job', language_code='es', title='Diseñador'
        )

        english_jobs = [
            {
                'objectID': 'job-ET1', 'id': 1, 'external_id': 'ET1', 'name': 'Engineer',
                'description': '', 'skills': [], 'job_postings': [], 'industry_names': [],
                'industries': [], 'similar_jobs': [], 'b2c_opt_in': False, 'job_sources': []
            },
            {
                'objectID': 'job-ET2', 'id': 2, 'external_id': 'ET2', 'name': 'Designer',
                'description': '', 'skills': [], 'job_postings': [], 'industry_names': [],
                'industries': [], 'similar_jobs': [], 'b2c_opt_in': False, 'job_sources': []
            }
        ]

        spanish_jobs = create_localized_job_records(english_jobs, 'es')

        assert len(spanish_jobs) == 2
        assert spanish_jobs[0]['name'] == 'Ingeniero'
        assert spanish_jobs[0]['metadata_language'] == 'es'
        assert spanish_jobs[1]['name'] == 'Diseñador'
        assert spanish_jobs[1]['metadata_language'] == 'es'

    def test_handles_partial_translations(self):
        """Test gracefully handles missing translations."""
        Job.objects.create(external_id='ET1', name='Engineer')
        TaxonomyTranslation.objects.create(
            external_id='ET1', content_type='job', language_code='es', title='Ingeniero'
        )

        english_jobs = [{
            'objectID': 'job-ET1', 'id': 1, 'external_id': 'ET1', 'name': 'Engineer',
            'description': '', 'skills': [{'name': 'Python'}], 'job_postings': [],
            'industry_names': ['IT'], 'industries': [], 'similar_jobs': ['Architect'],
            'b2c_opt_in': False, 'job_sources': []
        }]

        # No skill/industry translations
        spanish_jobs = create_localized_job_records(english_jobs, 'es')

        # Should fall back to English for missing translations
        assert spanish_jobs[0]['name'] == 'Ingeniero'  # Translated
        assert spanish_jobs[0]['skills'][0]['name'] == 'Python'  # Fallback
        assert spanish_jobs[0]['industry_names'][0] == 'IT'  # Fallback
        assert spanish_jobs[0]['similar_jobs'][0] == 'Architect'  # Fallback
        assert spanish_jobs[0]['metadata_language'] == 'es'

    def test_adds_metadata_language_field(self):
        """Test metadata_language field is added to translated jobs."""
        job = Job.objects.create(external_id='ET123', name='Engineer')

        english_jobs = [{
            'objectID': 'job-ET123',
            'id': 1,
            'external_id': 'ET123',
            'name': 'Engineer',
            'description': 'Desc',
            'skills': [],
            'job_postings': [],
            'industry_names': [],
            'industries': [],
            'similar_jobs': [],
            'b2c_opt_in': False,
            'job_sources': []
        }]

        spanish_jobs = create_localized_job_records(english_jobs, 'es')

        assert 'metadata_language' in spanish_jobs[0]
        assert spanish_jobs[0]['metadata_language'] == 'es'

    def test_returns_empty_list_when_no_jobs(self):
        """Test returns empty list when no jobs provided."""
        result = create_localized_job_records([], 'es')

        assert result == []

    def test_logs_progress_every_thousand_records(self, caplog, monkeypatch):
        """Test progress log branch is hit when processing every 1000th record."""
        english_jobs = [
            {
                'objectID': f'job-{idx}',
                'id': idx,
                'external_id': f'ET{idx}',
                'name': 'Engineer',
                'description': '',
                'skills': [],
                'job_postings': [],
                'industry_names': [],
                'industries': [],
                'similar_jobs': [],
                'b2c_opt_in': False,
                'job_sources': [],
            }
            for idx in range(1, 1001)
        ]

        monkeypatch.setattr(
            algolia_utils,
            'translate_job_record',
            lambda english_job, *_: {
                **english_job,
                'metadata_language': 'es',
            }
        )

        caplog.set_level(logging.INFO)
        result = create_localized_job_records(english_jobs, 'es')

        assert len(result) == 1000
        assert any('Translated 1000/1000 jobs to es' in record.message for record in caplog.records)

    def test_ignores_unexpected_translation_content_type(self, monkeypatch):
        """Test unknown translation content types do not break localization flow."""
        english_jobs = [{
            'objectID': 'job-ET1',
            'id': 1,
            'external_id': 'ET1',
            'name': 'Engineer',
            'description': '',
            'skills': [],
            'job_postings': [],
            'industry_names': [],
            'industries': [],
            'similar_jobs': [],
            'b2c_opt_in': False,
            'job_sources': [],
        }]

        # Include a translation record with an unexpected content_type so that
        # `if ct in prefetched` follows the False branch.
        unknown_trans = SimpleNamespace(content_type='unknown', external_id='X1')

        class FakeTranslationQuerySet:
            def __init__(self, values):
                self.values = values

            def filter(self, *args, **kwargs):
                return self

            def __iter__(self):
                return iter(self.values)

        monkeypatch.setattr(
            TaxonomyTranslation.objects,
            'filter',
            lambda *args, **kwargs: FakeTranslationQuerySet([unknown_trans]),
        )

        monkeypatch.setattr(
            algolia_utils,
            'build_name_translation_maps',
            lambda *_args, **_kwargs: {'job': {}, 'skill': {}, 'industry': {}},
        )
        monkeypatch.setattr(
            algolia_utils,
            'translate_job_record',
            lambda english_job, *_: {**english_job, 'metadata_language': 'es'},
        )

        localized = create_localized_job_records(english_jobs, 'es')

        assert len(localized) == 1
        assert localized[0]['metadata_language'] == 'es'


@pytest.mark.django_db
class TestIndexJobsDataInAlgolia:
    """Tests for full index build flow with localized records."""

    def test_indexes_english_and_localized_jobs(self, monkeypatch):
        """Test indexing appends localized records for each configured language."""
        client = MagicMock()
        monkeypatch.setattr(algolia_utils, 'AlgoliaClient', MagicMock(return_value=client))

        english_jobs = [{'objectID': 'job-ET1', 'name': 'Engineer', 'metadata_language': 'en'}]
        monkeypatch.setattr(algolia_utils, 'fetch_jobs_data', lambda: list(english_jobs))
        monkeypatch.setattr(algolia_utils, 'TAXONOMY_TRANSLATION_LOCALES', ['es', 'fr'])

        def _create_localized(jobs_data, language_code):
            return [{'objectID': f'job-ET1-{language_code}', 'name': 'Engineer', 'metadata_language': language_code}]

        monkeypatch.setattr(algolia_utils, 'create_localized_job_records', _create_localized)

        index_jobs_data_in_algolia()

        client.set_index_settings.assert_called_once()
        indexed_objects = client.replace_all_objects.call_args[0][0]
        assert len(indexed_objects) == 3
        assert {obj['metadata_language'] for obj in indexed_objects} == {'en', 'es', 'fr'}

    def test_only_english_records_passed_to_create_localized(self, monkeypatch):
        """Test create_localized_job_records always receives only English records.

        Regression test: previously jobs_data was mutated in-place so the second
        language iteration would receive English + first-language records, causing
        translated records to be re-translated.
        """
        client = MagicMock()
        monkeypatch.setattr(algolia_utils, 'AlgoliaClient', MagicMock(return_value=client))

        english_jobs = [
            {'objectID': 'job-ET1', 'name': 'Engineer', 'metadata_language': 'en'},
        ]
        monkeypatch.setattr(algolia_utils, 'fetch_jobs_data', lambda: list(english_jobs))
        monkeypatch.setattr(algolia_utils, 'TAXONOMY_TRANSLATION_LOCALES', ['es', 'fr'])

        received_inputs = []

        def _create_localized(jobs_data, language_code):
            received_inputs.append((language_code, list(jobs_data)))
            return [{'objectID': f'job-ET1-{language_code}', 'metadata_language': language_code}]

        monkeypatch.setattr(algolia_utils, 'create_localized_job_records', _create_localized)

        index_jobs_data_in_algolia()

        # Both calls must have received only the single English record.
        for lang, jobs_passed in received_inputs:
            assert len(jobs_passed) == 1, (
                f'create_localized_job_records for {lang!r} received {len(jobs_passed)} records '
                f'instead of 1 English record; translated records may be leaking into subsequent iterations.'
            )
            assert jobs_passed[0]['metadata_language'] == 'en'

    def test_uses_settings_locales_when_available(self, monkeypatch):
        """Runtime settings should override module-level default locales."""
        client = MagicMock()
        monkeypatch.setattr(algolia_utils, 'AlgoliaClient', MagicMock(return_value=client))
        monkeypatch.setattr(algolia_utils, 'fetch_jobs_data', lambda: [{'objectID': 'job-ET1', 'metadata_language': 'en'}])
        monkeypatch.setattr(algolia_utils, 'TAXONOMY_TRANSLATION_LOCALES', ['fr'])
        monkeypatch.setattr(algolia_utils.settings, 'TAXONOMY_TRANSLATION_LOCALES', ['es'], raising=False)

        received_languages = []

        def _create_localized(_jobs_data, language_code):
            received_languages.append(language_code)
            return [{'objectID': f'job-ET1-{language_code}', 'metadata_language': language_code}]

        monkeypatch.setattr(algolia_utils, 'create_localized_job_records', _create_localized)

        index_jobs_data_in_algolia()

        assert received_languages == ['es']


@pytest.mark.django_db
class TestFetchJobsData:
    """Tests for english jobs serialization payload."""

    def test_adds_metadata_language_to_serialized_jobs(self, monkeypatch):
        """Test serialized jobs include metadata_language='en'."""
        Job.objects.create(external_id='ET1', name='Engineer')

        monkeypatch.setattr(algolia_utils, 'fetch_and_combine_job_details', lambda _qs: {})
        monkeypatch.setattr(algolia_utils, 'combine_industry_skills', lambda: {})
        monkeypatch.setattr(algolia_utils, 'get_job_ids', lambda _qs: set())
        monkeypatch.setattr(JobSkills, 'get_whitelisted_job_skill_qs', classmethod(lambda cls: JobSkills.objects.none()))
        monkeypatch.setattr(
            IndustryJobSkill,
            'get_whitelisted_job_skill_qs',
            classmethod(lambda cls: IndustryJobSkill.objects.none())
        )

        class DummySerializer:
            """Serializer stub for deterministic test payload."""

            def __init__(self, *args, **kwargs):
                self.data = [{'objectID': 'job-ET1', 'name': 'Engineer'}]

        monkeypatch.setattr(algolia_utils, 'JobSerializer', DummySerializer)

        jobs = fetch_jobs_data()

        assert jobs == [
            {'objectID': 'job-ET1', 'name': 'Engineer', 'metadata_language': 'en', 'language_sort_priority': 0}
        ]


class TestTranslateSkillDictExternalId:
    """Extra tests for external_id-first skill translation behavior."""

    def test_prefers_external_id_translation_over_name(self):
        """When both keys exist, external_id mapping should win."""
        skill = {'external_id': 'ES123', 'name': 'Python'}
        name_maps = {'skill': {'ES123': 'Python (ID)', 'Python': 'Python (Name)'}}

        result = translate_skill_dict(skill, name_maps)

        assert result['name'] == 'Python (ID)'


class TestBuildNameTranslationMapsExternalId:
    """Extra tests for branch coverage in name map builder."""

    def test_skill_external_id_map_when_name_missing(self, monkeypatch):
        """Build maps should include external_id key even if name is falsey."""
        translation = SimpleNamespace(external_id='ES123', title='Python (ID)')
        prefetched = {'job': [], 'skill': [translation], 'industry': []}

        monkeypatch.setattr(Job.objects, 'exclude', lambda *args, **kwargs: [])
        monkeypatch.setattr(Industry.objects, 'exclude', lambda *args, **kwargs: [])
        monkeypatch.setattr(
            Skill.objects,
            'exclude',
            lambda *args, **kwargs: [SimpleNamespace(external_id='ES123', name='')],
        )

        maps = build_name_translation_maps('es', prefetched_translations=prefetched)

        assert maps['skill']['ES123'] == 'Python (ID)'
        assert '' not in maps['skill']


class TestAlgoliaCoreUtils:
    """Coverage tests for core helper utilities in algolia utils."""

    def test_calculate_jaccard_similarity_for_empty_sets(self):
        """Empty sets should return 0.0 via ZeroDivisionError path."""
        assert algolia_utils.calculate_jaccard_similarity(set(), set()) == 0.0

    def test_calculate_jaccard_similarity_for_non_empty_sets(self):
        """Non-empty sets should compute Jaccard similarity."""
        result = algolia_utils.calculate_jaccard_similarity({'a', 'b'}, {'b', 'c'})
        assert result == 1 / 3

    def test_insert_item_in_ordered_queue_replaces_tail_when_full(self):
        """Better item in full queue should be inserted and tail popped."""
        queue = deque([5, 3, 1], maxlen=3)

        algolia_utils.insert_item_in_ordered_queue(queue, 4)

        assert list(queue) == [5, 4, 3]

    def test_insert_item_in_ordered_queue_appends_when_space(self):
        """If no insertion point but queue has room, item should append."""
        queue = deque([5, 4], maxlen=3)

        algolia_utils.insert_item_in_ordered_queue(queue, 1)

        assert list(queue) == [5, 4, 1]

    def test_insert_item_in_ordered_queue_noop_when_full_and_low_priority(self):
        """If full and item is lower than all entries, queue is unchanged."""
        queue = deque([5, 4, 3], maxlen=3)

        algolia_utils.insert_item_in_ordered_queue(queue, 1)

        assert list(queue) == [5, 4, 3]

    def test_calculate_job_recommendations_adds_similar_jobs(self):
        """Similar jobs list should be present, bounded to 3, and exclude self."""
        jobs_data = {
            'Job A': {'skills': {'python', 'sql'}},
            'Job B': {'skills': {'python', 'sql', 'aws'}},
            'Job C': {'skills': {'java'}},
            'Job D': {'skills': {'python'}},
        }

        result = algolia_utils.calculate_job_recommendations(jobs_data)

        assert 'similar_jobs' in result['Job A']
        assert 'Job A' not in result['Job A']['similar_jobs']
        assert len(result['Job A']['similar_jobs']) <= 3

    def test_calculate_job_skills_builds_skill_set_per_job(self, monkeypatch):
        """Job skill names should be converted to sets per job."""
        jobs = [SimpleNamespace(name='Job A'), SimpleNamespace(name='Job B')]

        class FakeJobsQuerySet:
            def all(self):
                return jobs

        class FakeSkillQuerySet:
            def __init__(self):
                self.current_job = None

            def filter(self, job):
                self.current_job = job
                return self

            def values_list(self, *_args, **_kwargs):
                mapping = {
                    'Job A': ['Python', 'SQL'],
                    'Job B': ['Java'],
                }
                return mapping[self.current_job.name]

        monkeypatch.setattr(
            JobSkills,
            'get_whitelisted_job_skill_qs',
            classmethod(lambda _cls: FakeSkillQuerySet()),
        )

        result = algolia_utils.calculate_job_skills(FakeJobsQuerySet())

        assert result == {
            'Job A': {'skills': {'Python', 'SQL'}},
            'Job B': {'skills': {'Java'}},
        }

    def test_fetch_and_combine_job_details_calls_both_stages(self, monkeypatch):
        """Pipeline should call calculate_job_skills then recommendations."""
        marker_qs = object()
        skills_data = {'Job A': {'skills': {'Python'}}}
        final_data = {'Job A': {'skills': {'Python'}, 'similar_jobs': []}}

        monkeypatch.setattr(algolia_utils, 'calculate_job_skills', lambda qs: skills_data if qs is marker_qs else {})
        monkeypatch.setattr(
            algolia_utils,
            'calculate_job_recommendations',
            lambda jobs_data: final_data if jobs_data is skills_data else {},
        )

        result = algolia_utils.fetch_and_combine_job_details(marker_qs)

        assert result == final_data

    def test_combine_industry_skills_constructs_mapping(self, monkeypatch):
        """Industry-to-skills mapping should be built from queryset chains."""
        industries = [SimpleNamespace(name='IT'), SimpleNamespace(name='Finance')]

        class FakeIndustrySkillQS:
            def __init__(self):
                self.current_industry = None
                self.mapping = {
                    'IT': ['Python', 'Cloud'],
                    'Finance': ['Excel'],
                }

            def filter(self, industry):
                self.current_industry = industry.name
                return self

            def values_list(self, *_args, **_kwargs):
                return self

            def annotate(self, **_kwargs):
                return self

            def order_by(self, *_args, **_kwargs):
                return self

            def distinct(self):
                return self

            def __getitem__(self, item):
                return self.mapping[self.current_industry][item]

        monkeypatch.setattr(Industry.objects, 'all', lambda: industries)
        monkeypatch.setattr(
            IndustryJobSkill,
            'get_whitelisted_job_skill_qs',
            classmethod(lambda _cls: FakeIndustrySkillQS()),
        )

        result = algolia_utils.combine_industry_skills()

        assert result == {
            'IT': ['Python', 'Cloud'],
            'Finance': ['Excel'],
        }

    def test_get_job_ids_collects_ids_from_batches(self):
        """Batched job id collection should aggregate all values."""

        class FakeSlice:
            def __init__(self, values):
                self.values = values

            def exists(self):
                return bool(self.values)

            def values_list(self, *_args, **_kwargs):
                return self.values

        class FakeQuerySet:
            def __init__(self, values):
                self.values = values

            def all(self):
                return self

            def __getitem__(self, item):
                return FakeSlice(self.values[item.start:item.stop])

        result = algolia_utils.get_job_ids(FakeQuerySet([1, 2, 3]))

        assert result == {1, 2, 3}
