"""
Validate that utility functions are working properly.
"""
import copy
import logging

import ddt
import mock
import responses
from edx_django_utils.cache import TieredCache
from pytest import fixture, mark, raises
from testfixtures import LogCapture

from taxonomy import models, utils
from taxonomy.choices import ProductTypes
from taxonomy.constants import ENGLISH
from taxonomy.emsi.client import EMSISkillsApiClient
from taxonomy.exceptions import SkipProductProcessingError, TaxonomyAPIError
from taxonomy.models import CourseSkills, Industry, Job, JobSkills, Skill, Translation, XBlockSkillData, XBlockSkills
from test_utils import factories
from test_utils.constants import COURSE_KEY, PROGRAM_UUID, USAGE_KEY
from test_utils.decorators import mock_api_response
from test_utils.mocks import MockCourse, MockProgram, MockXBlock, mock_as_dict
from test_utils.sample_responses.skills import SKILLS_EMSI_CLIENT_RESPONSE, SKILLS_EMSI_RESPONSE
from test_utils.testcase import TaxonomyTestCase


@mark.django_db
@ddt.ddt
class TestUtils(TaxonomyTestCase):
    """
    Validate utility functions.
    """
    django_assert_num_queries = None

    def setUp(self):
        """
        Instantiate skills and other objects for tests.
        """
        super(TestUtils, self).setUp()
        self.skill = factories.SkillFactory()
        TieredCache.dangerous_clear_all_tiers()

    @fixture(autouse=True)
    def setup(self, django_assert_num_queries):
        """
        Instantiate fixtures.
        """
        self.django_assert_num_queries = django_assert_num_queries

    def test_blacklist_course_skill(self):
        """
        Validate that blacklist_course_skill works as expected.
        """
        factories.CourseSkillsFactory(course_key=COURSE_KEY, skill_id=self.skill.id)
        utils.blacklist_course_skill(course_key=COURSE_KEY, skill_id=self.skill.id)

        course_skill = models.CourseSkills.objects.get(
            course_key=COURSE_KEY, skill_id=self.skill.id,
        )
        assert course_skill.is_blacklisted is True

    def test_remove_course_skill_from_blacklist(self):
        """
        Validate that remove_course_skill_from_blacklist works as expected.
        """
        # Create a blacklisted course skill.
        factories.CourseSkillsFactory(course_key=COURSE_KEY, skill_id=self.skill.id, is_blacklisted=True)
        utils.remove_course_skill_from_blacklist(course_key=COURSE_KEY, skill_id=self.skill.id)

        course_skill = models.CourseSkills.objects.get(
            course_key=COURSE_KEY, skill_id=self.skill.id
        )
        assert course_skill.is_blacklisted is not True

    def test_is_course_skill_blacklisted(self):
        """
        Validate that is_course_skill_blacklisted works as expected.
        """
        # Create a Black listed course skill.
        factories.CourseSkillsFactory(course_key=COURSE_KEY, skill_id=self.skill.id, is_blacklisted=True)
        product_type = ProductTypes.Course

        assert utils.is_skill_blacklisted(COURSE_KEY, self.skill.id, product_type) is True
        assert utils.is_skill_blacklisted(COURSE_KEY, 0, product_type) is not True
        assert utils.is_skill_blacklisted('invalid+course-key', self.skill.id, product_type) is not True

        skill = factories.SkillFactory()
        assert utils.is_skill_blacklisted(COURSE_KEY, skill.id, product_type) is not True

    def test_update_course_skills_data(self):
        """
        Validate that update_product_skills_data works as expected.
        """
        black_listed_course_skill = factories.CourseSkillsFactory(course_key=COURSE_KEY, is_blacklisted=True)
        skills_count = Skill.objects.count()
        product_type = ProductTypes.Course
        utils.update_skills_data(
            key_or_uuid=COURSE_KEY,
            skill_external_id=black_listed_course_skill.skill.external_id,
            confidence=black_listed_course_skill.confidence,
            skill_data={
                'name': black_listed_course_skill.skill.name,
                'info_url': black_listed_course_skill.skill.info_url,
                'type_id': black_listed_course_skill.skill.type_id,
                'type_name': black_listed_course_skill.skill.type_name,
                'description': black_listed_course_skill.skill.description
            },
            product_type=product_type
        )

        updated_name = 'new_name'
        updated_info_url = 'new_url'
        updated_type_id = '1'
        updated_type_name = 'new_type'
        updated_description = 'new description'
        skill_data = {
            'name': updated_name,
            'info_url': updated_info_url,
            'type_id': updated_type_id,
            'type_name': updated_type_name,
            'description': updated_description
        }
        utils.update_skills_data(
            key_or_uuid=COURSE_KEY,
            skill_external_id=self.skill.external_id,
            confidence=0.9,
            skill_data=skill_data,
            product_type=product_type
        )

        # make sure no new `Skill` object created.
        assert Skill.objects.count() == skills_count

        # Make sure `CourseSkills` is no removed from the blacklist.
        assert utils.is_skill_blacklisted(COURSE_KEY, black_listed_course_skill.skill.id, product_type) is True
        course_skill = models.CourseSkills.objects.get(
            course_key=COURSE_KEY,
            skill=black_listed_course_skill.skill,
        )
        assert course_skill.is_blacklisted is True

        # Make sure that skill that was not black listed is added with no issues.
        assert utils.is_skill_blacklisted(COURSE_KEY, self.skill.id, product_type) is False
        assert models.CourseSkills.objects.filter(
            course_key=COURSE_KEY,
            skill=self.skill,
            is_blacklisted=False,
        ).exists()

        # Make sure the `Skill` object updated
        self.skill.refresh_from_db()
        assert self.skill.name == skill_data.get('name')
        assert self.skill.info_url == skill_data.get('info_url')
        assert self.skill.type_id == skill_data.get('type_id')
        assert self.skill.type_name == skill_data.get('type_name')
        assert self.skill.description == skill_data.get('description')

    def test_update_program_skills_data(self):
        """
        Validate that update_program_skills_data works as expected.
        """
        black_listed_program_skill = factories.ProgramSkillFactory(program_uuid=PROGRAM_UUID, is_blacklisted=True)
        skills_count = Skill.objects.count()
        product_type = ProductTypes.Program
        utils.update_skills_data(
            key_or_uuid=PROGRAM_UUID,
            skill_external_id=black_listed_program_skill.skill.external_id,
            confidence=black_listed_program_skill.confidence,
            skill_data={
                'name': black_listed_program_skill.skill.name,
                'info_url': black_listed_program_skill.skill.info_url,
                'type_id': black_listed_program_skill.skill.type_id,
                'type_name': black_listed_program_skill.skill.type_name,
                'description': black_listed_program_skill.skill.description
            },
            product_type=product_type
        )

        skill_data = {
            'name': 'new_name',
            'info_url': 'new_url',
            'type_id': '1',
            'type_name': 'new_type',
            'description': 'new description'
        }
        utils.update_skills_data(
            key_or_uuid=PROGRAM_UUID,
            skill_external_id=self.skill.external_id,
            confidence=0.9,
            skill_data=skill_data,
            product_type=product_type
        )

        # make sure no new `Skill` object created.
        assert Skill.objects.count() == skills_count

        # Make sure `ProgramSkill` is not removed from the blacklist.
        assert utils.is_skill_blacklisted(PROGRAM_UUID, black_listed_program_skill.skill.id, product_type) is True
        program_skill = models.ProgramSkill.objects.get(
            program_uuid=PROGRAM_UUID,
            skill=black_listed_program_skill.skill,
        )
        assert program_skill.is_blacklisted is True

        # Make sure that skill that was not black listed is added with no issues.
        assert utils.is_skill_blacklisted(PROGRAM_UUID, self.skill.id, product_type) is False
        assert models.ProgramSkill.objects.filter(
            program_uuid=PROGRAM_UUID,
            skill=self.skill,
            is_blacklisted=False,
        ).exists()

        # Make sure the `Skill` object updated
        self.skill.refresh_from_db()
        assert self.skill.name == skill_data.get('name')
        assert self.skill.info_url == skill_data.get('info_url')
        assert self.skill.type_id == skill_data.get('type_id')
        assert self.skill.type_name == skill_data.get('type_name')
        assert self.skill.description == skill_data.get('description')

    def test_update_xblock_skills_data(self):
        """
        Validate that update_xblock_skills_data works as expected.
        """
        xblock = factories.XBlockSkillsFactory(usage_key=USAGE_KEY)
        black_listed_xblock_skill = factories.XBlockSkillDataFactory(xblock=xblock, is_blacklisted=True)
        skills_count = Skill.objects.count()
        product_type = ProductTypes.XBlock
        utils.update_skills_data(
            key_or_uuid=USAGE_KEY,
            skill_external_id=black_listed_xblock_skill.skill.external_id,
            confidence=black_listed_xblock_skill.confidence,
            skill_data={
                'name': black_listed_xblock_skill.skill.name,
                'info_url': black_listed_xblock_skill.skill.info_url,
                'type_id': black_listed_xblock_skill.skill.type_id,
                'type_name': black_listed_xblock_skill.skill.type_name,
                'description': black_listed_xblock_skill.skill.description
            },
            product_type=product_type,
        )

        updated_name = 'new_name'
        updated_info_url = 'new_url'
        updated_type_id = '1'
        updated_type_name = 'new_type'
        updated_description = 'new description'
        hash_content = 'xyz'
        skill_data = {
            'name': updated_name,
            'info_url': updated_info_url,
            'type_id': updated_type_id,
            'type_name': updated_type_name,
            'description': updated_description
        }
        utils.update_skills_data(
            key_or_uuid=USAGE_KEY,
            skill_external_id=self.skill.external_id,
            confidence=0.9,
            skill_data=skill_data,
            product_type=product_type,
            hash_content=hash_content,
        )

        # Make sure no new `Skill` object is created.
        assert Skill.objects.count() == skills_count

        # Make sure hash_content is stored properly.
        assert XBlockSkills.objects.filter(
            usage_key=USAGE_KEY,
            hash_content=hash_content,
        ).exists()

        # Make sure `XBlockSkills` is not removed from the blacklist.
        assert utils.is_skill_blacklisted(
            xblock.id,
            black_listed_xblock_skill.skill.id,
            ProductTypes.XBlockData,
        ) is True
        xblock_skill = models.XBlockSkillData.objects.get(
            xblock=xblock,
            skill=black_listed_xblock_skill.skill,
        )
        assert xblock_skill.is_blacklisted

        # Make sure the skill that was not black listed is added with no issues.
        assert not utils.is_skill_blacklisted(xblock.id, self.skill.id, ProductTypes.XBlockData)
        assert models.XBlockSkillData.objects.filter(
            xblock=xblock,
            skill=self.skill,
            is_blacklisted=False,
        ).exists()

        # Make sure the `Skill` object is updated
        self.skill.refresh_from_db()
        assert self.skill.name == skill_data.get('name')
        assert self.skill.info_url == skill_data.get('info_url')
        assert self.skill.type_id == skill_data.get('type_id')
        assert self.skill.type_name == skill_data.get('type_name')
        assert self.skill.description == skill_data.get('description')

    def test_process_program_skills_data_missing_keys(self):
        """
        Validate that process_course_skills_data fails on missing fields in ProgramSkills.
        """
        sample_skill_data = copy.deepcopy({'data': [SKILLS_EMSI_CLIENT_RESPONSE['data'][0]]})
        del sample_skill_data['data'][0]['skill']['id']
        program = {'uuid': 'test-uuid'}
        product_type = ProductTypes.Program

        failures = utils.process_skills_data(program, sample_skill_data, False, product_type)
        assert len(failures) == 1
        assert failures[0] == ('test-uuid', '[TAXONOMY] Missing keys in skills data for key: test-uuid')

    def test_process_program_skills_data_invalid_confidence(self):
        """
        Validate that process_skills_data fails on having an invalid confidence field in ProgramSkills.
        """
        sample_skill_data = copy.deepcopy({'data': [SKILLS_EMSI_CLIENT_RESPONSE['data'][0]]})
        sample_skill_data['data'][0]['confidence'] = 'invalid-value'
        program = {'uuid': 'test-uuid'}
        product_type = ProductTypes.Program

        failures = utils.process_skills_data(program, sample_skill_data, False, product_type)
        assert len(failures) == 1
        assert failures[0] == ('test-uuid',
                               '[TAXONOMY] Invalid type for `confidence` in skills for key: test-uuid')

    def test_get_course_skills(self):
        """
        Validate that get_course_skills works as expected.
        """
        # Create 10 blacklisted course skill.
        factories.CourseSkillsFactory.create_batch(10, course_key=COURSE_KEY, is_blacklisted=True)

        # Create 5 course skill that are not blacklisted.
        factories.CourseSkillsFactory.create_batch(5, course_key=COURSE_KEY, is_blacklisted=False)

        # 1 query for fetching all 5 course skills and its associated skill.
        with self.django_assert_num_queries(1):
            course_skills = utils.get_whitelisted_product_skills(
                key_or_uuid=COURSE_KEY, product_type=ProductTypes.Course
            )
            skill_ids = [course_skill.skill.id for course_skill in course_skills]
            assert len(skill_ids) == 5

        # 1 query for fetching all 5 course skills and then 5 subsequent queries for fetching skill associated with
        # each of the 5 course skills.
        with self.django_assert_num_queries(6):
            course_skills = utils.get_whitelisted_product_skills(
                key_or_uuid=COURSE_KEY, product_type=ProductTypes.Course, prefetch_skills=False
            )
            skill_ids = [course_skill.skill.id for course_skill in course_skills]
            assert len(skill_ids) == 5

    def test_get_blacklisted_course_skills(self):
        """
        Validate that get_blacklisted_course_skills works as expected.
        """
        # Create 10 blacklisted course skill.
        factories.CourseSkillsFactory.create_batch(10, course_key=COURSE_KEY, is_blacklisted=True)

        # Create 5 course skill that are not blacklisted.
        factories.CourseSkillsFactory.create_batch(5, course_key=COURSE_KEY, is_blacklisted=False)

        # 1 query for fetching all 10 course skills and its associated skill.
        with self.django_assert_num_queries(1):
            blacklisted_course_skills = utils.get_blacklisted_course_skills(course_key=COURSE_KEY)
            skill_ids = [course_skill.skill.id for course_skill in blacklisted_course_skills]
            assert len(skill_ids) == 10

        # 1 query for fetching all 10 course skills and then 10 subsequent queries for fetching skill associated with
        # each of the 10 course skills.
        with self.django_assert_num_queries(11):
            blacklisted_course_skills = utils.get_blacklisted_course_skills(
                course_key=COURSE_KEY, prefetch_skills=False
            )
            skill_ids = [course_skill.skill.id for course_skill in blacklisted_course_skills]
            assert len(skill_ids) == 10

    def test_query_count_for_whitelisted_course_retrival(self):
        """
        Validate that `get_whitelisted_serialized_skills` retrieves all course related data in single query.
        """
        factories.CourseSkillsFactory.create_batch(
            2,
            course_key=COURSE_KEY,
            is_blacklisted=False,
            skill__category=None,
            skill__subcategory=None
        )
        with self.django_assert_num_queries(1):
            utils.get_whitelisted_serialized_skills(key_or_uuid=COURSE_KEY, product_type=ProductTypes.Course)

    def test_get_whitelisted_serialized_skills(self):
        """
        Validate that `get_whitelisted_serialized_skills` returns serialized skills in expected format.
        """
        factories.CourseSkillsFactory.create_batch(
            2,
            course_key=COURSE_KEY,
            is_blacklisted=False,
            skill__category=None,
            skill__subcategory=None
        )
        expected_skills = utils.get_whitelisted_product_skills(key_or_uuid=COURSE_KEY, product_type=ProductTypes.Course)
        expected_serialized_skills = [
            {
                'name': expected_skill.skill.name,
                'description': expected_skill.skill.description,
                'category': None,
                'subcategory': None,
            } for expected_skill in expected_skills
        ]

        actual_serialized_skills = utils.get_whitelisted_serialized_skills(
            key_or_uuid=COURSE_KEY, product_type=ProductTypes.Course
        )
        assert actual_serialized_skills == expected_serialized_skills

        factories.ProgramSkillFactory.create_batch(
            2,
            program_uuid=PROGRAM_UUID,
            is_blacklisted=False,
            skill__category=None,
            skill__subcategory=None
        )
        expected_skills = utils.get_whitelisted_product_skills(
            key_or_uuid=PROGRAM_UUID, product_type=ProductTypes.Program
        )
        expected_serialized_skills = [
            {
                'name': expected_skill.skill.name,
                'description': expected_skill.skill.description,
                'category': None,
                'subcategory': None,
            } for expected_skill in expected_skills
        ]

        actual_serialized_skills = utils.get_whitelisted_serialized_skills(
            key_or_uuid=PROGRAM_UUID, product_type=ProductTypes.Program
        )
        assert actual_serialized_skills == expected_serialized_skills

    def test_get_whitelisted_serialized_skills_cache_hit(self):
        """
        Validate that a cached result is returned on subsequent invocations of
        `get_whitelisted_serialized_skills()`.
        """
        factories.CourseSkillsFactory.create_batch(
            2,
            course_key=COURSE_KEY,
            is_blacklisted=False,
            skill__category=None,
            skill__subcategory=None
        )
        serialized_skills_first_result = utils.get_whitelisted_serialized_skills(
            key_or_uuid=COURSE_KEY, product_type=ProductTypes.Course
        )

        with mock.patch('taxonomy.utils.get_whitelisted_product_skills') as mock_get_course_skills:
            serialized_skills_next_result = utils.get_whitelisted_serialized_skills(
                key_or_uuid=COURSE_KEY, product_type=ProductTypes.Course
            )
            self.assertEqual(serialized_skills_first_result, serialized_skills_next_result)
            self.assertFalse(mock_get_course_skills.called)

    def test_get_course_jobs(self):
        """
        Validate that `get_course_jobs` works as expected.
        """
        course_skills = factories.CourseSkillsFactory(course_key=COURSE_KEY, is_blacklisted=False)
        jobskills = factories.JobSkillFactory.create_batch(5, skill=course_skills.skill)
        for jobskill in jobskills:
            factories.JobPostingsFactory(job=jobskill.job)

        expected_course_jobs = utils.get_course_jobs(course_key=COURSE_KEY, product_type=ProductTypes.Course)

        # course jobs should not be empty
        assert expected_course_jobs

        for course_job in expected_course_jobs:
            job_skill = JobSkills.objects.get(job__name=course_job.get('name'))
            job_posting = job_skill.job.jobpostings_set.first()

            # verify job posting data
            assert job_posting.median_salary == course_job.get('median_salary')
            assert job_posting.unique_postings == course_job.get('unique_postings')

            # verify that skill is associated with correct course
            assert CourseSkills.objects.filter(skill=job_skill.skill).exists()

            # verify that job is associated with correct skill
            assert job_skill.skill == course_skills.skill

    @mock.patch('taxonomy.utils.translate_text')
    def test_get_translated_course_description_with_updated_description_and_eng_lang(self, translate_mocked):
        """
        Validate that `get_translated_skill_attribute_val` updates Translation object if
         course description changes. Also verify that if source language is ENGLISH,
         than keep the original text in source and translated text field.
        """
        existing_course_description = "abc def"
        existing_translation = "translated text old"

        new_course_description = "ghi jkl"
        new_translation = "translated text new"
        product_type = ProductTypes.Course
        translate_mocked.return_value = {
            'SourceLanguageCode': ENGLISH,
            'TranslatedText': new_translation
        }
        factories.TranslationFactory(
            source_record_identifier=COURSE_KEY,
            source_model_field=utils.COURSE_METADATA_FIELDS_COMBINED,
            source_model_name=product_type,
            source_text=existing_course_description,
            translated_text=existing_translation,
            translated_text_language=ENGLISH,
            source_language=ENGLISH,
        )

        expected_translated_description = utils.get_translated_skill_attribute_val(
            COURSE_KEY, new_course_description, product_type
        )
        translation_record = Translation.objects.filter(
            source_model_name=product_type,
            source_model_field=utils.COURSE_METADATA_FIELDS_COMBINED,
            source_record_identifier=COURSE_KEY
        ).first()

        assert new_course_description == expected_translated_description
        assert translation_record.translated_text == new_course_description
        assert translate_mocked.call_count == 1

    @mock.patch('taxonomy.utils.translate_text')
    def test_get_translated_course_description_with_updated_description_and_non_eng_lang(self, translate_text_mocked):
        """
        Validate that `get_translated_skill_attribute_val` updates Translation object if
         course description changes. Also verify that if source language is NON-ENGLISH,
         than update the translated text field.
        """
        existing_course_description = "abc def"
        existing_translation = "translated text old"

        new_course_description = "ghi jkl"
        new_translation = "translated text new"
        product_type = ProductTypes.Course

        translate_text_mocked.return_value = {
            'SourceLanguageCode': 'AR',
            'TranslatedText': new_translation
        }
        factories.TranslationFactory(
            source_record_identifier=COURSE_KEY,
            source_model_field=utils.COURSE_METADATA_FIELDS_COMBINED,
            source_model_name=product_type,
            source_text=existing_course_description,
            translated_text=existing_translation,
            translated_text_language=ENGLISH,
            source_language=ENGLISH,
        )
        expected_translated_description = utils.get_translated_skill_attribute_val(
            COURSE_KEY, new_course_description, product_type
        )
        translation_record = Translation.objects.filter(
            source_model_name=product_type,
            source_model_field=utils.COURSE_METADATA_FIELDS_COMBINED,
            source_record_identifier=COURSE_KEY
        ).first()

        assert new_translation == expected_translated_description
        assert translation_record.translated_text == new_translation
        assert translate_text_mocked.call_count == 1

    @mock.patch('taxonomy.utils.translate_text')
    def test_get_translated_course_description_with_same_description(self, translate_text_mocked):
        """
        Validate that `get_translated_course_description` returns translated course_description
         and updates Translation object.
        """
        course_description = "abc def"
        product_type = ProductTypes.Course
        translated_course_description = "different text"
        translate_text_mocked.return_value = {
            'SourceLanguageCode': ENGLISH,
            'TranslatedText': translated_course_description,
        }
        trans = factories.TranslationFactory(
            source_record_identifier=COURSE_KEY,
            source_model_field=utils.COURSE_METADATA_FIELDS_COMBINED,
            source_model_name=product_type,
            source_text=course_description,
            translated_text=translated_course_description,
            translated_text_language=ENGLISH,
            source_language=ENGLISH,
        )

        expected_translated_description = utils.get_translated_skill_attribute_val(
            COURSE_KEY, course_description, product_type
        )
        translation_record = Translation.objects.filter(
            source_model_name=product_type,
            source_model_field=utils.COURSE_METADATA_FIELDS_COMBINED,
            source_record_identifier=COURSE_KEY
        ).exists()
        assert translation_record is True
        assert trans.translated_text == expected_translated_description
        assert trans.source_text == course_description
        assert translate_text_mocked.call_count == 0

    @mock.patch('taxonomy.utils.translate_text')
    def test_get_translated_course_description_error_for_new_record(self, translate_text_mocked):
        """
        Validate that `get_translated_skill_attribute_val` returns actual course_description
         if translate_text method returns None and does not create Translation object.
        """
        course_description = "abc def"
        product_type = ProductTypes.Course
        translate_text_mocked.return_value = {'SourceLanguageCode': '', 'TranslatedText': ''}
        expected_translated_description = utils.get_translated_skill_attribute_val(
            COURSE_KEY, course_description, product_type
        )
        translation_record = Translation.objects.filter(
            source_model_name=ProductTypes.Course,
            source_model_field='full_description',
            source_record_identifier=COURSE_KEY
        ).first()
        assert translation_record is None
        assert course_description == expected_translated_description
        assert translate_text_mocked.call_count == 1

    @mock.patch('taxonomy.utils.translate_text')
    def test_get_translated_course_description_error_for_existing_record(self, translate_text_mocked):
        """
        Validate that `get_translated_course_description` returns actual course_description
         if translate_text method returns None and does not update Translation object.
        """
        translate_text_mocked.return_value = {'SourceLanguageCode': '', 'TranslatedText': ''}
        course_description = "abc def"
        new_course_description = "jhi qlm"
        product_type = ProductTypes.Course
        translated_course_description = "different text"
        trans = factories.TranslationFactory(
            source_record_identifier=COURSE_KEY,
            source_model_field='full_description',
            source_model_name=ProductTypes.Course,
            source_text=course_description,
            translated_text=translated_course_description,
            translated_text_language=ENGLISH,
            source_language=ENGLISH,
        )

        expected_translated_description = utils.get_translated_skill_attribute_val(
            COURSE_KEY, new_course_description, product_type
        )
        translation_record = Translation.objects.filter(
            source_model_name=ProductTypes.Course,
            source_model_field='full_description',
            source_record_identifier=COURSE_KEY
        ).first()

        assert new_course_description == expected_translated_description
        assert trans.source_text == translation_record.source_text
        assert trans.translated_text == translation_record.translated_text
        assert translate_text_mocked.call_count == 1

    @mock.patch('taxonomy.utils.translate_text')
    def test_get_translated_course_description_success_for_new_record(self, translate_text_mocked):
        """
        Validate that `get_translated_skill_attribute_val` created Translation object if not already
        exist with the translated course description.
        """
        course_description = "abc def"
        product_type = ProductTypes.Course
        translated_course_description = "different text"
        translate_text_mocked.return_value = {
            'SourceLanguageCode': ENGLISH,
            'TranslatedText': translated_course_description,
        }
        expected_translated_description = utils.get_translated_skill_attribute_val(
            COURSE_KEY, course_description, product_type
        )
        translation_record = Translation.objects.filter(
            source_model_name=product_type,
            source_model_field='title:short_description:full_description',
            source_record_identifier=COURSE_KEY
        ).first()

        assert translation_record.translated_text == expected_translated_description
        assert translation_record.source_text == course_description
        assert translate_text_mocked.call_count == 1

    @mock.patch('taxonomy.utils.translate_text')
    def test_get_translated_course_description_success_for_new_record_and_non_eng_lang(self, translate_text_mocked):
        """
        Validate that `get_translated_skill_attribute_val` created Translation object if not already
        exist with the translated course description.
        """
        course_description = "abc def"
        product_type = ProductTypes.Course
        translated_course_description = "different text"
        translate_text_mocked.return_value = {
            'SourceLanguageCode': 'AR',
            'TranslatedText': translated_course_description,
        }
        expected_translated_description = utils.get_translated_skill_attribute_val(
            COURSE_KEY, course_description, product_type
        )
        translation_record = Translation.objects.filter(
            source_model_name=product_type,
            source_model_field=utils.COURSE_METADATA_FIELDS_COMBINED,
            source_record_identifier=COURSE_KEY
        ).first()

        assert translation_record.translated_text == expected_translated_description
        assert translation_record.source_text == course_description
        assert translate_text_mocked.call_count == 1

    @mock.patch("taxonomy.utils.AMAZON_TRANSLATION_ALLOWED_SIZE", 5)
    @mock.patch('taxonomy.utils.translate_text')
    def test_get_translated_course_description_success_for_new_record_with_large_text(self, translate_text_mocked):
        """
        Validate that `get_translated_skill_attribute_val` created Translation object if not already
        exist with the translated course description.
        """
        course_description = "<p>abc</p><span>def</span><br/><p>ghi</p>"
        product_type = ProductTypes.Course
        translated_course_description = "<p>abc</p><span>def</span><br/><p>ghi</p>"
        translate_text_mocked.return_value = {
            'SourceLanguageCode': ENGLISH,
            'TranslatedText': translated_course_description,
        }
        expected_translated_description = utils.get_translated_skill_attribute_val(
            COURSE_KEY, course_description, product_type
        )
        translation_record = Translation.objects.filter(
            source_model_name=product_type,
            source_model_field=utils.COURSE_METADATA_FIELDS_COMBINED,
            source_record_identifier=COURSE_KEY
        ).first()

        assert translation_record.translated_text == expected_translated_description
        assert translation_record.source_text == course_description
        assert translate_text_mocked.call_count == 5

    @mock.patch("taxonomy.utils.AMAZON_TRANSLATION_ALLOWED_SIZE", 5)
    @mock.patch('taxonomy.utils.translate_text')
    def test_get_translated_course_description_with_updated_description_and_large_text(self, translate_mocked):
        """
        Validate that `get_translated_skill_attribute_val` updates Translation object if
         course description changes. Also verify that if source language is ENGLISH,
         than keep the original text in source and translated text field.
        """
        existing_course_description = "<span>abc</span>"
        existing_translation = "<span>abc</span>"

        new_course_description = "<p>abc</p><span>def</span>"
        new_translation = "<p>abc</p><span>def</span>"
        product_type = ProductTypes.Course
        translate_mocked.return_value = {
            'SourceLanguageCode': ENGLISH,
            'TranslatedText': new_translation
        }
        factories.TranslationFactory(
            source_record_identifier=COURSE_KEY,
            source_model_field=utils.COURSE_METADATA_FIELDS_COMBINED,
            source_model_name=product_type,
            source_text=existing_course_description,
            translated_text=existing_translation,
            translated_text_language=ENGLISH,
            source_language=ENGLISH,
        )

        expected_translated_description = utils.get_translated_skill_attribute_val(
            COURSE_KEY, new_course_description, product_type
        )
        translation_record = Translation.objects.filter(
            source_model_name=product_type,
            source_model_field=utils.COURSE_METADATA_FIELDS_COMBINED,
            source_record_identifier=COURSE_KEY
        ).first()

        assert new_course_description == expected_translated_description
        assert translation_record.translated_text == new_course_description
        assert translate_mocked.call_count == 3

    def test_xblock_update_with_no_changes(self):
        """
        Validate extract_metadata_from_attr_text and
        verify_xblock_existence_and_content_changes returns correct data and
        flag.
        """
        text = 'some text'
        xblock = factories.XBlockSkillsFactory(usage_key=USAGE_KEY)
        extra_data = utils.extract_metadata_from_attr_text(text, ProductTypes.XBlock)
        # XBlock with new text should not raise skip processing error.
        utils.verify_xblock_existence_and_content_changes(extra_data, USAGE_KEY)
        assert 'hash_content' in extra_data
        xblock.hash_content = extra_data['hash_content']
        xblock.auto_processed = True
        xblock.save()

        # xblock with same content should skip processing.
        with raises(SkipProductProcessingError):
            utils.verify_xblock_existence_and_content_changes(extra_data, USAGE_KEY)

    def test_skills_from_similar_product(self):
        """
        Check that skills from product with same content is reused.
        """
        text = 'some text'
        xblock = factories.XBlockSkillsFactory(usage_key=USAGE_KEY)
        extra_data = utils.extract_metadata_from_attr_text(text, ProductTypes.XBlock)
        xblock.hash_content = extra_data['hash_content']
        xblock.auto_processed = True
        xblock.save()
        # XBlock with new text should not raise skip processing error.
        other_usage_key = USAGE_KEY.replace("edx", "xde")
        skills = utils.xblock_with_same_content(extra_data, other_usage_key)
        assert skills is not None

    @mock.patch('taxonomy.utils.EMSISkillsApiClient.get_product_skills')
    @mock.patch('taxonomy.utils.get_translated_skill_attribute_val')
    def test_refresh_xblock_skills_no_change_or_invalid_product_type_skipped(
            self,
            get_translated_description_mock,
            get_xblock_skills_mock
    ):
        """
        Validate that `refresh_product_skills` only calls API if content has
        changed and if product is valid.
        """
        get_xblock_skills_mock.return_value = SKILLS_EMSI_CLIENT_RESPONSE
        get_translated_description_mock.return_value = None
        product_type = ProductTypes.XBlock

        xblocks = ["invalid_product_type"]
        xblock = mock_as_dict(MockXBlock())
        for _ in range(3):
            xblocks.append({
                'key': xblock.key,
                'content_type': xblock.content_type,
                'content': xblock.content,
            })

        utils.refresh_product_skills(xblocks, True, product_type)

        assert get_translated_description_mock.call_count == 0
        # it should be processed only once as the same content for same xblock
        # is passed multiple times for valid ProductTypes
        assert get_xblock_skills_mock.call_count == 1

        # changed content should trigger processing
        new_data = [{
            'key': xblock.key,
            'content_type': xblock.content_type,
            'content': mock_as_dict(MockXBlock()).content,
        }]

        utils.refresh_product_skills(new_data, True, product_type)
        assert get_xblock_skills_mock.call_count == 2

    @mock.patch('taxonomy.utils.EMSISkillsApiClient.get_product_skills')
    @mock.patch('taxonomy.utils.get_translated_skill_attribute_val')
    def test_refresh_xblock_skills_same_content_reuse_skills(
            self,
            get_translated_description_mock,
            get_xblock_skills_mock
    ):
        """
        Validate that `refresh_product_skills` reuses skills from other xblock
        if it has same content.
        """
        get_xblock_skills_mock.return_value = SKILLS_EMSI_CLIENT_RESPONSE
        get_translated_description_mock.return_value = None
        product_type = ProductTypes.XBlock

        xblocks = []
        for _ in range(4):
            xblock = mock_as_dict(MockXBlock())
            xblocks.append(
                {'key': xblock.key, 'content_type': xblock.content_type, 'content': xblock.content},
            )
        # update last xblock content to be same as the first one.
        xblocks[-1]['content'] = xblocks[0]['content']

        success_count, failure_count = utils.refresh_product_skills(xblocks, True, product_type)
        assert get_translated_description_mock.call_count == 0
        # it should be call the api for last xblock.
        assert get_xblock_skills_mock.call_count == 3
        self.assertEqual(failure_count, 0)
        self.assertEqual(success_count, 4)

        def compare_xblocks(xblock_key_1, xblock_key_2):
            xblock_skill_1 = XBlockSkills.objects.get(usage_key=xblock_key_1)
            xblock_skill_2 = XBlockSkills.objects.get(usage_key=xblock_key_2)
            self.assertListEqual(list(xblock_skill_1.skills.values()), list(xblock_skill_2.skills.values()))
            fields_to_compare = (
                "skill",
                "verified_count",
                "ignored_count",
                "confidence",
                "verified",
                "is_blacklisted"
            )
            self.assertListEqual(
                list(xblock_skill_1.xblockskilldata_set.values(*fields_to_compare)),
                list(xblock_skill_2.xblockskilldata_set.values(*fields_to_compare))
            )
        compare_xblocks(xblocks[0]['key'], xblocks[-1]['key'])

        # update existing xblock with content similar to any other xblock
        # it should reuse the tags from the other xblock
        xblocks[1]['content'] = xblocks[2]['content']
        # update verification data to verified that it is also copied over.
        XBlockSkillData.objects.filter(xblock__usage_key=xblocks[2]['key']).update(
            verified_count=10,
            ignored_count=1,
            verified=True
        )

        success_count, failure_count = utils.refresh_product_skills([xblocks[1]], True, product_type)
        # translation as well as api should not be called
        assert get_translated_description_mock.call_count == 0
        assert get_xblock_skills_mock.call_count == 3
        self.assertEqual(failure_count, 0)
        self.assertEqual(success_count, 1)
        compare_xblocks(xblocks[1]['key'], xblocks[2]['key'])

    @mock_api_response(
        method=responses.POST,
        url=EMSISkillsApiClient.API_BASE_URL + '/extract',
        json=SKILLS_EMSI_RESPONSE,
    )
    @mock.patch('taxonomy.utils.get_translated_skill_attribute_val')
    @mock.patch('taxonomy.emsi.client.sleep')
    @mock.patch('taxonomy.emsi.client.time')
    def test_refresh_course_skills_rate_limit_emsi_api_calls(
            self,
            time_mock,
            time_sleep_mock,
            get_translated_description_mock,
    ):
        """
        Validate that `refresh_product_skills` rate limits API calls to EMSI.
        """
        self.mock_access_token()
        time_mock.return_value = 1  # Freeze time for the test.
        get_translated_description_mock.return_value = None
        time_sleep_mock.return_value = None

        EMSISkillsApiClient.REQUEST_COUNT_CACHE.clear()
        product_type = ProductTypes.Course

        courses = []
        for _ in range(6):
            course = mock_as_dict(MockCourse())
            courses.append({
                'uuid': course.uuid,
                'key': course.key,
                'title': course.title,
                'short_description': course.short_description,
                'full_description': course.full_description,
            })

        utils.refresh_product_skills(courses, False, product_type)

        # It should be called at the 6th request made in the current second
        assert time_sleep_mock.call_count == 1

    def test_refresh_program_skills_skipped(self):
        """
        Validate that `refresh_skills` shows skipped_programs_count properly.
        """
        program = mock_as_dict(MockProgram())
        overview = {'overview': None, 'uuid': program.uuid}
        program.__getitem__.side_effect = overview.__getitem__
        assert program['overview'] is None
        product_type = ProductTypes.Program

        with LogCapture(level=logging.INFO) as log_capture:
            utils.refresh_product_skills([program], False, product_type)
            messages = [record.msg for record in log_capture.records]
            self.assertIn('Total %s Skipped: %s', messages[0])

    @mock.patch('taxonomy.utils.translate_text')
    @mock.patch('taxonomy.utils.EMSISkillsApiClient.get_product_skills')
    def test_refresh_program_skills_api_error(self, mock_emsi_skills_data, mock_translate):
        """
        Validate that `refresh_program_skills` handles TaxonomyAPIError
        """
        mock_emsi_skills_data.side_effect = TaxonomyAPIError
        mock_translate.return_value = {'SourceLanguageCode': '', 'TranslatedText': ''}
        program = mock_as_dict(MockProgram())

        with LogCapture(level=logging.INFO) as log_capture:
            utils.refresh_product_skills([program], False, ProductTypes.Program)
            messages = [record.msg for record in log_capture.records]
            self.assertIn(f'[TAXONOMY] API Error for key: {program["uuid"]}', messages)

    @mock.patch('taxonomy.utils.translate_text')
    @mock.patch('taxonomy.utils.process_skills_data')
    @mock.patch('taxonomy.utils.EMSISkillsApiClient.get_product_skills')
    def test_refresh_program_skills_broad_exception(
            self,
            mock_emsi_skills_data,
            mock_skills_data,
            mock_translate,
    ):
        """
        Validate that `refresh_skills` handles broad exception.
        """
        mock_emsi_skills_data.return_value = SKILLS_EMSI_CLIENT_RESPONSE
        mock_skills_data.side_effect = Exception
        mock_translate.return_value = {'SourceLanguageCode': '', 'TranslatedText': ''}
        program = mock_as_dict(MockProgram())

        with LogCapture(level=logging.INFO) as log_capture:
            utils.refresh_product_skills([program], False, ProductTypes.Program)
            messages = [record.msg for record in log_capture.records]
            self.assertIn(f'[TAXONOMY] Exception for key: {program["uuid"]} Error: ', messages)

    @mock_api_response(
        method=responses.POST,
        url=EMSISkillsApiClient.API_BASE_URL + '/extract',
        json=SKILLS_EMSI_RESPONSE,
    )
    @mock.patch('taxonomy.utils.translate_text')
    @mock.patch('taxonomy.emsi.client.sleep', return_value=None)
    @mock.patch('taxonomy.emsi.client.time')
    def test_refresh_program_skills_rate_limit_emsi_api_calls(
            self,
            time_mock,
            time_sleep_mock,
            mock_translate,
    ):
        """
        Validate that `refresh_program_skills` rate limits API calls to EMSI.
        """
        self.mock_access_token()
        time_mock.return_value = 1  # Freeze time for the test.
        mock_translate.return_value = {'SourceLanguageCode': '', 'TranslatedText': ''}
        EMSISkillsApiClient.REQUEST_COUNT_CACHE.clear()

        programs = []
        for _ in range(6):
            program = mock_as_dict(MockProgram())
            programs.append(program)

        utils.refresh_product_skills(programs, False, ProductTypes.Program)

        # It should be called at the 6th request made in the current second
        assert time_sleep_mock.call_count == 1

    def test_get_whitelisted_serialized_skills_with_category_details(self):
        """
        Validate that `get_whitelisted_serialized_skills` returns serialized skills with category
        and subcategory information in expected format.
        """
        skill_category = factories.SkillCategoryFactory(name='Category 1')
        skill_subcategory = factories.SkillSubCategoryFactory(
            name='Subcategory 1',
            category=skill_category
        )
        for count in range(3):
            skill = factories.SkillFactory(
                name=f'Skill {count + 1}',
                description=f'Skill {count + 1}',
                category=skill_category if count % 2 == 0 else None,  # do not add category for other skill
                subcategory=skill_subcategory,
            )
            factories.CourseSkillsFactory(
                skill=skill,
                course_key=COURSE_KEY,
                is_blacklisted=False
            )
        category_data = {
            'category': {
                'name': 'Category 1'
            },
            'subcategory': {
                'name': 'Subcategory 1',
                'category': {
                    'name': 'Category 1'
                },
            }}
        expected_data = [
            {
                'name': 'Skill 1',
                'description': 'Skill 1',
                **category_data
            },
            {
                'name': 'Skill 2',
                'description': 'Skill 2',
                **category_data,
                'category': None,
            },
            {
                'name': 'Skill 3',
                'description': 'Skill 3',
                **category_data
            },
        ]
        skill_details = utils.get_whitelisted_serialized_skills(
            key_or_uuid=COURSE_KEY, product_type=ProductTypes.Course
        )

        assert len(skill_details) == 3  # Skill 2 with missing category is not present in the results
        assert skill_details == expected_data

    def test_duplicate_xblock_skills(self):
        """
        Validate that `duplicate_xblock_skills` works as expected.
        """
        xblock = factories.XBlockSkillsFactory(usage_key=USAGE_KEY)
        factories.XBlockSkillDataFactory.create_batch(4, xblock=xblock)
        dup_usage_key = 'block-v1:edx+DemoX+Demo_course+type@video+block@dup-uuid'
        utils.duplicate_xblock_skills(USAGE_KEY, dup_usage_key)
        dup_xblock = XBlockSkills.objects.filter(usage_key=dup_usage_key).first()
        assert dup_xblock is not None
        assert XBlockSkillData.objects.filter(xblock=dup_xblock).count() == 4

    def test_duplicate_xblock_skills_incorrect_source(self):
        """
        Validate that `duplicate_xblock_skills` stops for incorrect source usage_key.
        """
        xblock = factories.XBlockSkillsFactory(usage_key=USAGE_KEY)
        factories.XBlockSkillDataFactory.create_batch(4, xblock=xblock)
        dup_usage_key = 'block-v1:edx+DemoX+Demo_course+type@video+block@dup-uuid'
        incorrect_source = xblock.usage_key[:-1]
        with LogCapture(level=logging.INFO) as log_capture:
            utils.duplicate_xblock_skills(incorrect_source, dup_usage_key)
            messages = [record.msg for record in log_capture.records]
            self.assertIn(f'[TAXONOMY] Source xblock: {incorrect_source} not found', messages[0])
        dup_xblock = XBlockSkills.objects.filter(usage_key=dup_usage_key).first()
        self.assertIsNone(dup_xblock)
        assert XBlockSkillData.objects.filter(xblock=dup_xblock).count() == 0

    def test_duplicate_xblock_skills_existing_usage_key(self):
        """
        Validate that `duplicate_xblock_skills` stops if usage_key already exists.
        """
        xblock = factories.XBlockSkillsFactory(usage_key=USAGE_KEY)
        existing_xblock = factories.XBlockSkillsFactory()
        factories.XBlockSkillDataFactory.create_batch(4, xblock=xblock)
        with LogCapture(level=logging.INFO) as log_capture:
            utils.duplicate_xblock_skills(USAGE_KEY, existing_xblock.usage_key)
            messages = [record.msg for record in log_capture.records]
            self.assertIn(f'[TAXONOMY] XBlock with usage_key: {existing_xblock.usage_key} already exists!', messages[0])
        assert XBlockSkillData.objects.filter(xblock=existing_xblock).count() == 0

    def test_duplicate_model_instance_with_dates(self):
        """
        Validate that models with/without created and modified dates.
        """
        xblock = factories.XBlockSkillsFactory(usage_key=USAGE_KEY)
        xblock.usage_key = "new"
        new_instance = utils.duplicate_model_instance(xblock)
        xblock = XBlockSkills.objects.filter(usage_key=USAGE_KEY).first()
        assert xblock.id != new_instance.id
        assert xblock.created < new_instance.created
        assert xblock.modified < new_instance.modified
        industry = factories.IndustryFactory()
        original_industry = Industry.objects.get(id=industry.id)
        # test model without created and modified attribute
        new_industry = utils.duplicate_model_instance(industry)
        assert original_industry.id != new_instance.id
        assert not hasattr(new_industry, "created")
        assert not hasattr(new_industry, "modified")

    @ddt.data(None, 'some text')
    @mock.patch('taxonomy.utils.chat_completion')
    def test_generate_and_store_job_description(self, description, mock_chat_completion):
        """
        Validate that `generate_and_store_job_description` handles a null job description correctly
        """
        job = factories.JobFactory()
        mock_chat_completion.return_value = description
        utils.generate_and_store_job_description(job.external_id, job.name)
        updated_job = Job.objects.get(external_id=job.external_id)
        if description:
            assert updated_job.description == description
        else:
            assert updated_job.description == job.description
