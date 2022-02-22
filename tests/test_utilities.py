"""
Validate that utility functions are working properly.
"""
import ddt
import mock
from pytest import fixture, mark

from taxonomy import models, utils
from taxonomy.constants import ENGLISH
from taxonomy.models import CourseSkills, JobSkills, Skill, Translation
from test_utils import factories
from test_utils.constants import COURSE_KEY
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

        assert utils.is_course_skill_blacklisted(COURSE_KEY, self.skill.id) is True
        assert utils.is_course_skill_blacklisted(COURSE_KEY, 0) is not True
        assert utils.is_course_skill_blacklisted('invalid+course-key', self.skill.id) is not True

        skill = factories.SkillFactory()
        assert utils.is_course_skill_blacklisted(COURSE_KEY, skill.id) is not True

    def test_update_skills_data(self):
        """
        Validate that update_skills_data works as expected.
        """
        black_listed_course_skill = factories.CourseSkillsFactory(course_key=COURSE_KEY, is_blacklisted=True)
        skills_count = Skill.objects.count()
        utils.update_skills_data(
            course_key=COURSE_KEY,
            skill_external_id=black_listed_course_skill.skill.external_id,
            confidence=black_listed_course_skill.confidence,
            skill_data={
                'name': black_listed_course_skill.skill.name,
                'info_url': black_listed_course_skill.skill.info_url,
                'type_id': black_listed_course_skill.skill.type_id,
                'type_name': black_listed_course_skill.skill.type_name,
                'description': black_listed_course_skill.skill.description
            }
        )

        updated_name = 'new_name'
        updated_info_url = 'new_url'
        updated_type_id = '1'
        updated_type_name = 'new_type'
        updated_description = 'new description'
        utils.update_skills_data(
            course_key=COURSE_KEY,
            skill_external_id=self.skill.external_id,
            confidence=0.9,
            skill_data={
                'name': updated_name,
                'info_url': updated_info_url,
                'type_id': updated_type_id,
                'type_name': updated_type_name,
                'description': updated_description
            }
        )

        # make sure no new `Skill` object created.
        assert Skill.objects.count() == skills_count

        # Make sure `CourseSkills` is no removed from the blacklist.
        assert utils.is_course_skill_blacklisted(COURSE_KEY, black_listed_course_skill.skill.id) is True
        course_skill = models.CourseSkills.objects.get(
            course_key=COURSE_KEY,
            skill=black_listed_course_skill.skill,
        )
        assert course_skill.is_blacklisted is True

        # Make sure that skill that was not black listed is added with no issues.
        assert utils.is_course_skill_blacklisted(COURSE_KEY, self.skill.id) is False
        assert models.CourseSkills.objects.filter(
            course_key=COURSE_KEY,
            skill=self.skill,
            is_blacklisted=False,
        ).exists()

        # Make sure the `Skill` object updated
        self.skill.refresh_from_db()
        assert self.skill.name == updated_name
        assert self.skill.info_url == updated_info_url
        assert self.skill.type_id == updated_type_id
        assert self.skill.type_name == updated_type_name
        assert self.skill.description == updated_description

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
            course_skills = utils.get_whitelisted_course_skills(course_key=COURSE_KEY)
            skill_ids = [course_skill.skill.id for course_skill in course_skills]
            assert len(skill_ids) == 5

        # 1 query for fetching all 5 course skills and then 5 subsequent queries for fetching skill associated with
        # each of the 5 course skills.
        with self.django_assert_num_queries(6):
            course_skills = utils.get_whitelisted_course_skills(course_key=COURSE_KEY, prefetch_skills=False)
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

    def test_get_whitelisted_serialized_skills(self):
        """
        Validate that `get_whitelisted_serialized_skills` returns serialized skills in expected format.
        """
        factories.CourseSkillsFactory.create_batch(2, course_key=COURSE_KEY, is_blacklisted=False)
        expected_skills = utils.get_whitelisted_course_skills(course_key=COURSE_KEY)
        expected_serialized_skills = [
            {
                'name': expected_skill.skill.name,
                'description': expected_skill.skill.description
            } for expected_skill in expected_skills
        ]

        actual_serialized_skills = utils.get_whitelisted_serialized_skills(course_key=COURSE_KEY)
        assert actual_serialized_skills == expected_serialized_skills

    def test_get_course_jobs(self):
        """
        Validate that `get_course_jobs` works as expected.
        """
        course_skills = factories.CourseSkillsFactory(course_key=COURSE_KEY, is_blacklisted=False)
        jobskills = factories.JobSkillFactory.create_batch(5, skill=course_skills.skill)
        for jobskill in jobskills:
            factories.JobPostingsFactory(job=jobskill.job)

        expected_course_jobs = utils.get_course_jobs(course_key=COURSE_KEY)

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
        Validate that `get_translated_course_description` updates Translation object if
         course description changes. Also verify that if source language is ENGLISH,
         than keep the original text in source and translated text field.
        """
        existing_course_description = "abc def"
        existing_translation = "translated text old"

        new_course_description = "ghi jkl"
        new_translation = "translated text new"
        translate_mocked.return_value = {
            'SourceLanguageCode': ENGLISH,
            'TranslatedText': new_translation
        }
        factories.TranslationFactory(
            source_record_identifier=COURSE_KEY,
            source_model_field='full_description',
            source_model_name='Course',
            source_text=existing_course_description,
            translated_text=existing_translation,
            translated_text_language=ENGLISH,
            source_language=ENGLISH,
        )

        expected_translated_description = utils.get_translated_course_description(COURSE_KEY, new_course_description)
        translation_record = Translation.objects.filter(
            source_model_name='Course',
            source_model_field='full_description',
            source_record_identifier=COURSE_KEY
        ).first()

        assert new_course_description == expected_translated_description
        assert translation_record.translated_text == new_course_description
        assert translate_mocked.call_count == 1

    @mock.patch('taxonomy.utils.translate_text')
    def test_get_translated_course_description_with_updated_description_and_non_eng_lang(self, translate_text_mocked):
        """
        Validate that `get_translated_course_description` updates Translation object if
         course description changes. Also verify that if source language is NON-ENGLISH,
         than update the translated text field.
        """
        existing_course_description = "abc def"
        existing_translation = "translated text old"

        new_course_description = "ghi jkl"
        new_translation = "translated text new"
        translate_text_mocked.return_value = {
            'SourceLanguageCode': 'AR',
            'TranslatedText': new_translation
        }
        factories.TranslationFactory(
            source_record_identifier=COURSE_KEY,
            source_model_field='full_description',
            source_model_name='Course',
            source_text=existing_course_description,
            translated_text=existing_translation,
            translated_text_language=ENGLISH,
            source_language=ENGLISH,
        )
        expected_translated_description = utils.get_translated_course_description(COURSE_KEY, new_course_description)
        translation_record = Translation.objects.filter(
            source_model_name='Course',
            source_model_field='full_description',
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
        translated_course_description = "different text"
        translate_text_mocked.return_value = {
            'SourceLanguageCode': ENGLISH,
            'TranslatedText': translated_course_description,
        }
        trans = factories.TranslationFactory(
            source_record_identifier=COURSE_KEY,
            source_model_field='full_description',
            source_model_name='Course',
            source_text=course_description,
            translated_text=translated_course_description,
            translated_text_language=ENGLISH,
            source_language=ENGLISH,
        )

        expected_translated_description = utils.get_translated_course_description(COURSE_KEY, course_description)
        translation_record = Translation.objects.filter(
            source_model_name='Course',
            source_model_field='full_description',
            source_record_identifier=COURSE_KEY
        ).exists()
        assert translation_record is True
        assert trans.translated_text == expected_translated_description
        assert trans.source_text == course_description
        assert translate_text_mocked.call_count == 0

    @mock.patch('taxonomy.utils.translate_text')
    def test_get_translated_course_description_error_for_new_record(self, translate_text_mocked):
        """
        Validate that `get_translated_course_description` returns actual course_description
         if translate_text method returns None and does not create Translation object.
        """
        course_description = "abc def"
        translate_text_mocked.return_value = {'SourceLanguageCode': '', 'TranslatedText': ''}
        expected_translated_description = utils.get_translated_course_description(COURSE_KEY, course_description)
        translation_record = Translation.objects.filter(
            source_model_name='Course',
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
        translated_course_description = "different text"
        trans = factories.TranslationFactory(
            source_record_identifier=COURSE_KEY,
            source_model_field='full_description',
            source_model_name='Course',
            source_text=course_description,
            translated_text=translated_course_description,
            translated_text_language=ENGLISH,
            source_language=ENGLISH,
        )

        expected_translated_description = utils.get_translated_course_description(COURSE_KEY, new_course_description)
        translation_record = Translation.objects.filter(
            source_model_name='Course',
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
        Validate that `get_translated_course_description` created Translation object if not already
        exist with the translated course description.
        """
        course_description = "abc def"
        translated_course_description = "different text"
        translate_text_mocked.return_value = {
            'SourceLanguageCode': ENGLISH,
            'TranslatedText': translated_course_description,
        }
        expected_translated_description = utils.get_translated_course_description(COURSE_KEY, course_description)
        translation_record = Translation.objects.filter(
            source_model_name='Course',
            source_model_field='full_description',
            source_record_identifier=COURSE_KEY
        ).first()

        assert translation_record.translated_text == expected_translated_description
        assert translation_record.source_text == course_description
        assert translate_text_mocked.call_count == 1

    @mock.patch('taxonomy.utils.translate_text')
    def test_get_translated_course_description_success_for_new_record_and_non_eng_lang(self, translate_text_mocked):
        """
        Validate that `get_translated_course_description` created Translation object if not already
        exist with the translated course description.
        """
        course_description = "abc def"
        translated_course_description = "different text"
        translate_text_mocked.return_value = {
            'SourceLanguageCode': 'AR',
            'TranslatedText': translated_course_description,
        }
        expected_translated_description = utils.get_translated_course_description(COURSE_KEY, course_description)
        translation_record = Translation.objects.filter(
            source_model_name='Course',
            source_model_field='full_description',
            source_record_identifier=COURSE_KEY
        ).first()

        assert translation_record.translated_text == expected_translated_description
        assert translation_record.source_text == course_description
        assert translate_text_mocked.call_count == 1

    @mock.patch("taxonomy.utils.AMAZON_TRANSLATION_ALLOWED_SIZE", 5)
    @mock.patch('taxonomy.utils.translate_text')
    def test_get_translated_course_description_success_for_new_record_with_large_text(self, translate_text_mocked):
        """
        Validate that `get_translated_course_description` created Translation object if not already
        exist with the translated course description.
        """
        course_description = "<p>abc</p><span>def</span><br/><p>ghi</p>"
        translated_course_description = "<p>abc</p><span>def</span><br/><p>ghi</p>"
        translate_text_mocked.return_value = {
            'SourceLanguageCode': ENGLISH,
            'TranslatedText': translated_course_description,
        }
        expected_translated_description = utils.get_translated_course_description(COURSE_KEY, course_description)
        translation_record = Translation.objects.filter(
            source_model_name='Course',
            source_model_field='full_description',
            source_record_identifier=COURSE_KEY
        ).first()

        assert translation_record.translated_text == expected_translated_description
        assert translation_record.source_text == course_description
        assert translate_text_mocked.call_count == 5

    @mock.patch("taxonomy.utils.AMAZON_TRANSLATION_ALLOWED_SIZE", 5)
    @mock.patch('taxonomy.utils.translate_text')
    def test_get_translated_course_description_with_updated_description_and_large_text(self, translate_mocked):
        """
        Validate that `get_translated_course_description` updates Translation object if
         course description changes. Also verify that if source language is ENGLISH,
         than keep the original text in source and translated text field.
        """
        existing_course_description = "<span>abc</span>"
        existing_translation = "<span>abc</span>"

        new_course_description = "<p>abc</p><span>def</span>"
        new_translation = "<p>abc</p><span>def</span>"
        translate_mocked.return_value = {
            'SourceLanguageCode': ENGLISH,
            'TranslatedText': new_translation
        }
        factories.TranslationFactory(
            source_record_identifier=COURSE_KEY,
            source_model_field='full_description',
            source_model_name='Course',
            source_text=existing_course_description,
            translated_text=existing_translation,
            translated_text_language=ENGLISH,
            source_language=ENGLISH,
        )

        expected_translated_description = utils.get_translated_course_description(COURSE_KEY, new_course_description)
        translation_record = Translation.objects.filter(
            source_model_name='Course',
            source_model_field='full_description',
            source_record_identifier=COURSE_KEY
        ).first()

        assert new_course_description == expected_translated_description
        assert translation_record.translated_text == new_course_description
        assert translate_mocked.call_count == 3
