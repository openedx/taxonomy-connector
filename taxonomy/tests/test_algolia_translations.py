# -*- coding: utf-8 -*-
"""
Tests for Algolia translation utilities.
"""
import pytest

from taxonomy.algolia.utils import (
    build_name_translation_maps,
    create_localized_job_records,
    translate_industries_array,
    translate_job_record,
    translate_skill_dict,
)
from taxonomy.models import Industry, Job, Skill, TaxonomyTranslation


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


@pytest.mark.django_db
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


@pytest.mark.django_db
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
        assert result['external_id'] == 'ET123'

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
        assert spanish_jobs[0]['name'] == 'Ingeniero'
        assert spanish_jobs[0]['description'] == 'Descripción'
        assert spanish_jobs[0]['metadata_language'] == 'es'

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
