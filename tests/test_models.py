# -*- coding: utf-8 -*-
"""
Tests for the taxonomy models.
"""
from unittest.mock import patch

import pytest
from pytest import mark

from django.conf import settings
from django.core.exceptions import ValidationError
from django.test import TestCase

from taxonomy.models import B2CJobAllowList, Industry, Job, JobPostings, SkillValidationConfiguration
from taxonomy.signals.handlers import generate_job_description
from taxonomy.utils import generate_and_store_job_description
from test_utils import factories
from test_utils.mocks import MockCourse, MockCourseRun
from test_utils.providers import DiscoveryCourseMetadataProvider


@mark.django_db
class TestJobPostings(TestCase):
    """
    Tests for the ``JobPostings`` model.
    """

    def setUp(self):
        super(TestJobPostings, self).setUp()
        self.job_title = 'Software Engineer'
        self.job = Job.objects.create(name=self.job_title)
        self.median_salary = 6500000
        self.median_posting_duration = 28
        self.unique_postings = 1345
        self.unique_companies = 148
        self.job_posting = JobPostings.objects.create(
            job=self.job,
            median_salary=self.median_salary,
            median_posting_duration=self.median_posting_duration,
            unique_postings=self.unique_postings,
            unique_companies=self.unique_companies
        )

    def test_string_representation(self):
        """
        Test the string representation of the JobPostings model.
        """
        expected_str = '<Job postings for job: {}, have a median_salary: ${}, median_posting_duration: {}, ' \
                       'unique_postings: {}, unique hiring companies: {} >'.format(
                           self.job_title, self.median_salary, self.median_posting_duration, self.unique_postings,
                           self.unique_companies)

        expected_repr = '<JobPosting id="{0}" job="{1!r}" median_salary="${2!r}" median_posting_duration="{3!r}" ' \
                        'unique_postings="{4!r} unique_companies={5!r}">'.format(
                            self.job_posting.id, self.job, self.median_salary, self.median_posting_duration,
                            self.unique_postings, self.unique_companies)

        assert expected_str == self.job_posting.__str__()
        assert expected_repr == self.job_posting.__repr__()


@mark.django_db
class TestSkill(TestCase):
    """
    Tests for the ``Skill`` model.
    """

    def test_string_representation(self):
        """
        Test the string representation of the Skill model.
        """
        skill = factories.SkillFactory()
        expected_str = '<Skill name="{}" external_id="{}">'.format(skill.name, skill.external_id)
        expected_repr = '<Skill id="{}" name="{}">'.format(skill.id, skill.name)

        assert expected_str == skill.__str__()
        assert expected_repr == skill.__repr__()


@mark.django_db
class TestCourseSkills(TestCase):
    """
    Tests for the ``CourseSkills`` model.
    """

    def test_string_representation(self):
        """
        Test the string representation of the CourseSkill model.
        """
        course_skill = factories.CourseSkillsFactory()
        expected_str = '<CourseSkills name="{}" course_key="{}">'.format(
            course_skill.skill.name, course_skill.course_key
        )
        expected_repr = '<CourseSkills id="{0}" skill="{1!r}">'.format(course_skill.id, course_skill.skill)

        assert expected_str == course_skill.__str__()
        assert expected_repr == course_skill.__repr__()


@mark.django_db
class TestCourseRunXBlockSkillsTracker(TestCase):
    """
    Tests for the ``CourseRunXBlockSkillsTracker`` model.
    """

    def test_string_representation(self):
        """
        Test the string representation of the CourseSkill model.
        """
        course_run = factories.CourseRunXBlockSkillsTrackerFactory()
        expected_str = '<CourseRunXBlockSkillsTracker course_run_key="{}">'.format(
            course_run.course_run_key
        )
        expected_repr = '<CourseRunXBlockSkillsTracker id="{0}">'.format(course_run.id)

        assert expected_str == course_run.__str__()
        assert expected_repr == course_run.__repr__()


@mark.django_db
class TestXBlockSkills(TestCase):
    """
    Tests for the ``XBlockSkills`` model.
    """

    def test_string_representation(self):
        """
        Test the string representation of the XBlockSkills model.
        """
        xblock_skills = factories.XBlockSkillsFactory()
        expected_str = '<XBlockSkills usage_key="{}">'.format(
            xblock_skills.usage_key
        )
        expected_repr = '<XBlockSkills id="{0}">'.format(xblock_skills.id)

        assert expected_str == xblock_skills.__str__()
        assert expected_repr == xblock_skills.__repr__()


@mark.django_db
class TestXBlockSkillData(TestCase):
    """
    Tests for the ``XBlockSkillData`` model.
    """

    def test_string_representation(self):
        """
        Test the string representation of the XBlockSkillData model.
        """
        xblock_skill_through = factories.XBlockSkillDataFactory()
        expected_str = '<XBlockSkillData usage_key="{}" skill="{}" verified="{}">'.format(
            xblock_skill_through.xblock.usage_key,
            xblock_skill_through.skill.name,
            xblock_skill_through.verified,
        )
        expected_repr = '<XBlockSkillData id="{0}">'.format(xblock_skill_through.id)

        assert expected_str == xblock_skill_through.__str__()
        assert expected_repr == xblock_skill_through.__repr__()


@mark.django_db
class TestJobSkills(TestCase):
    """
    Tests for the ``JobSkills`` model.
    """

    def test_string_representation(self):
        """
        Test the string representation of the JobSkills model.
        """
        job_skill = factories.JobSkillFactory()
        expected_str = '<JobSkills job="{}" skill="{}" significance="{}">'.format(
            job_skill.job.name, job_skill.skill.name, job_skill.significance
        )
        expected_repr = '<JobSkills id={} job="{}" skill="{}" significance="{}">'.format(
            job_skill.id, job_skill.job.name, job_skill.skill.name, job_skill.significance
        )

        assert expected_str == job_skill.__str__()
        assert expected_repr == job_skill.__repr__()


@mark.django_db
class TestIndustryJobSkills(TestCase):
    """
    Tests for the ``IndustryJobSkill`` model.
    """

    def test_string_representation(self):
        """
        Test the string representation of the IndustryJobSkill model.
        """
        ijs = factories.IndustryJobSkillFactory()
        expected_str = '<IndustryJobSkills industry="{}" job="{}" skill="{}" significance="{}">'.format(
            ijs.industry.name, ijs.job.name, ijs.skill.name, ijs.significance
        )
        expected_repr = '<IndustryJobSkills id={} industry="{}" job="{}" skill="{}" significance="{}">'.format(
            ijs.id, ijs.industry.name, ijs.job.name, ijs.skill.name, ijs.significance
        )

        assert expected_str == ijs.__str__()
        assert expected_repr == ijs.__repr__()


@mark.django_db
class TestProgramSkill(TestCase):
    """
    Tests for the ``ProgramSkill`` model.
    """

    def test_string_representation(self):
        """
        Test the string representation of the ProgramSkill model.
        """
        program_skill = factories.ProgramSkillFactory()
        expected_str = '<ProgramSkill name="{}" program_uuid="{}">'.format(
            program_skill.skill.name, program_skill.program_uuid
        )
        expected_repr = '<ProgramSkill id="{0}" skill="{1!r}">'.format(program_skill.id, program_skill.skill)

        assert expected_str == str(program_skill)
        assert expected_repr == repr(program_skill)


@mark.django_db
class TestTranslation(TestCase):
    """
    Tests for the ``Translation`` model.
    """

    def test_string_representation(self):
        """
        Test the string representation of the Translation model.
        """
        translation = factories.TranslationFactory()
        expected_str = '<Translation for source_record_identifier={} source_language={} translated_text_language={}>'.\
            format(
                translation.source_record_identifier,
                translation.source_language,
                translation.translated_text_language
            )
        expected_repr = '<Translation source_model_name="{}" source_model_field="{}" source_record_identifier="{}" ' \
            'source_text="{}" source_language="{}" translated_text="{}" translated_text_language="{}">'.format(
                translation.source_model_name, translation.source_model_field, translation.source_record_identifier,
                translation.source_text, translation.source_language, translation.translated_text,
                translation.translated_text_language)

        assert expected_str == translation.__str__()
        assert expected_repr == translation.__repr__()


@mark.django_db
class TestSkillCategory(TestCase):
    """
    Tests for the ``SkillCategory`` model.
    """

    def test_string_representation(self):
        """
        Test the string representation of the SkillCategory model.
        """
        skill_category = factories.SkillCategoryFactory()
        expected_str = '<SkillCategory id="{}" name="{}">'.format(skill_category.id, skill_category.name)
        expected_repr = expected_str

        assert expected_str == skill_category.__str__()
        assert expected_repr == skill_category.__repr__()


@mark.django_db
class TestRefreshProgramSkillConfig(TestCase):
    """
    Tests for the ``RefreshProgramSkillConfig`` model.
    """

    def test_string_representation(self):
        """
        Test the string representation of the RefreshProgramSkillConfig model.
        """
        program_skill_config = factories.RefreshProgramSkillsConfigFactory()
        expected_str = '<RefreshProgramSkillsConfig arguments="{}">'.format(program_skill_config.arguments)
        expected_repr = '<RefreshProgramSkillsConfig id="{}">'.format(program_skill_config.id)

        assert expected_str == program_skill_config.__str__()
        assert expected_repr == program_skill_config.__repr__()


@mark.django_db
class TestRefreshCourseSkillConfig(TestCase):
    """
    Tests for the ``RefreshCourseSkillConfig`` model.
    """

    def test_string_representation(self):
        """
        Test the string representation of the RefreshCourseSkillConfig model.
        """
        course_skill_config = factories.RefreshCourseSkillsConfigFactory()
        expected_str = '<RefreshCourseSkillsConfig arguments="{}">'.format(course_skill_config.arguments)
        expected_repr = '<RefreshCourseSkillsConfig id="{}">'.format(course_skill_config.id)

        assert expected_str == course_skill_config.__str__()
        assert expected_repr == course_skill_config.__repr__()


@mark.django_db
class TestRefreshXBlockSkillConfig(TestCase):
    """
    Tests for the ``RefreshXBlockSkillsConfig`` model.
    """

    def test_string_representation(self):
        """
        Test the string representation of the RefreshXBlockSkillsConfig model.
        """
        xblock_skill_config = factories.RefreshXBlockSkillsConfigFactory()
        expected_str = '<RefreshXBlockSkillsConfig arguments="{}">'.format(xblock_skill_config.arguments)
        expected_repr = '<RefreshXBlockSkillsConfig id="{}">'.format(xblock_skill_config.id)

        assert expected_str == xblock_skill_config.__str__()
        assert expected_repr == xblock_skill_config.__repr__()


@mark.django_db
class TestJob(TestCase):
    """
    Tests for the ``Job`` model.
    """

    def test_string_representation(self):
        """
        Test the string representation of the Job model.
        """
        job = factories.JobFactory()
        expected_str = '<Job title={}>'.format(job.name)
        expected_repr = '<Job id="{}" name="{}" external_id="{}" description="{}">'.format(
            job.id,
            job.name,
            job.external_id,
            job.description
        )

        assert expected_str == job.__str__()
        assert expected_repr == job.__repr__()

    @pytest.mark.use_signals
    @patch('taxonomy.openai.client.requests.post')
    @patch('taxonomy.utils.generate_and_store_job_description', wraps=generate_and_store_job_description)
    @patch('taxonomy.signals.handlers.generate_job_description.delay', wraps=generate_job_description)
    def test_chat_completion_is_called(   # pylint: disable=invalid-name
            self,
            mocked_generate_job_description_task,
            mocked_generate_and_store_job_description,
            mock_requests
    ):
        """
        Verify that complete flow works as expected when a Job model object is created.
        """
        ai_response = 'One who manages a Computer Network.'
        mock_requests.return_value.json.return_value = {
            "role": "assistant",
            "content": ai_response
        }

        job_external_id = '1111'
        job_name = 'Network Admin'

        Job(external_id=job_external_id, name=job_name).save()
        job = Job.objects.get(external_id=job_external_id)

        assert job.description == ai_response
        mocked_generate_job_description_task.assert_called_once_with(job_external_id, job_name)
        mocked_generate_and_store_job_description.assert_called_once_with(job_external_id, job_name)
        mock_requests.assert_called_once()

    @pytest.mark.use_signals
    @patch('taxonomy.utils.chat_completion')
    @patch('taxonomy.utils.generate_and_store_job_description', wraps=generate_and_store_job_description)
    @patch('taxonomy.signals.handlers.generate_job_description.delay', wraps=generate_job_description)
    def test_multiple_job_creation(   # pylint: disable=invalid-name
            self,
            mocked_generate_job_description_task,
            mocked_generate_and_store_job_description,
            mocked_chat_completion
    ):
        """
        Verify that complete flow works as expected when a Job model object is created.
        """
        mocked_chat_completion.side_effect = lambda prompt: prompt

        factories.JobFactory.create_batch(10)

        assert Job.objects.count() == 10

        for job in Job.objects.all():
            prompt = settings.JOB_DESCRIPTION_PROMPT.format(job_name=job.name)
            assert job.description == prompt

            assert mocked_generate_and_store_job_description.call_count == 10
            assert mocked_chat_completion.call_count == 10
            mocked_generate_job_description_task.assert_any_call(job.external_id, job.name)
            mocked_generate_and_store_job_description.assert_any_call(job.external_id, job.name)
            mocked_chat_completion.assert_any_call(prompt)

    @pytest.mark.use_signals
    @patch('taxonomy.signals.handlers.generate_job_description.delay')
    def test_task_triggered_only_if_job_has_name(self, mocked_generate_job_description_task):
        """
        Verify that celery task triggers only when a job has name.
        """
        Job(external_id='11111').save()
        mocked_generate_job_description_task.assert_not_called()

    @pytest.mark.use_signals
    @patch('taxonomy.signals.handlers.generate_job_description.delay')
    def test_task_does_not_triggered_if_job_has_description(self, mocked_generate_job_description_task):
        """
        Verify that celery task does not triggered when a job already has description.
        """
        Job(external_id='11111', name='job name', description='I am description').save()
        mocked_generate_job_description_task.assert_not_called()

    def test_get_whitelisted_job_skills(self):
        """
        Validate get_whitelisted_job_skills returns only job skills that have not been blacklisted.
        """
        job = factories.JobFactory.create()
        factories.JobSkillFactory.create_batch(10, job=job, is_blacklisted=True)
        factories.JobSkillFactory.create_batch(5, job=job, is_blacklisted=False)
        factories.IndustryJobSkillFactory.create_batch(10, job=job, is_blacklisted=True)
        factories.IndustryJobSkillFactory.create_batch(5, job=job, is_blacklisted=False)

        # Make sure there were only 2 queries made to fetch the data, one for job skills
        # and another for industry job skills.
        with self.assertNumQueries(2):
            job_skills, industry_job_skills = job.get_whitelisted_job_skills()
            assert len(job_skills) == 5
            assert len(industry_job_skills) == 5

    def test_get_blacklisted_job_skills(self):
        """
        Validate get_blacklisted_job_skills returns only job skills that have been blacklisted.
        """
        job = factories.JobFactory.create()
        factories.JobSkillFactory.create_batch(10, job=job, is_blacklisted=True)
        factories.JobSkillFactory.create_batch(5, job=job, is_blacklisted=False)
        factories.IndustryJobSkillFactory.create_batch(10, job=job, is_blacklisted=True)
        factories.IndustryJobSkillFactory.create_batch(5, job=job, is_blacklisted=False)

        # Make sure there were only 2 queries made to fetch the data, one for job skills
        # and another for industry job skills.
        with self.assertNumQueries(2):
            job_skills, industry_job_skills = job.get_blacklisted_job_skills()
            assert len(job_skills) == 10
            assert len(industry_job_skills) == 10

    def test_get_skills_disabled_prefetch(self):
        """
        Validate get_blacklisted_job_skills makes multiple queries if user wants to disable prefetch.
        """
        job = factories.JobFactory.create()
        factories.JobSkillFactory.create_batch(10, job=job, is_blacklisted=True)
        factories.JobSkillFactory.create_batch(5, job=job, is_blacklisted=False)
        factories.IndustryJobSkillFactory.create_batch(10, job=job, is_blacklisted=True)
        factories.IndustryJobSkillFactory.create_batch(5, job=job, is_blacklisted=False)

        # Make sure there were only 2 queries made to fetch the data, one for job skills
        # and another for industry job skills.
        with self.assertNumQueries(22):
            job_skills, industry_job_skills = job.get_blacklisted_job_skills(prefetch_skills=False)

            assert len([job_skill.skill.id for job_skill in job_skills]) == 10
            assert len([job_skill.skill.id for job_skill in industry_job_skills]) == 10

        with self.assertNumQueries(12):
            job_skills, industry_job_skills = job.get_whitelisted_job_skills(prefetch_skills=False)

            assert len([job_skill.skill.id for job_skill in job_skills]) == 5
            assert len([job_skill.skill.id for job_skill in industry_job_skills]) == 5

    def test_whitelist_job_skills(self):
        """
        Validate whitelist_job_skills removes skills from the blacklist.
        """
        job = factories.JobFactory.create()
        blacklisted_job_skills = factories.JobSkillFactory.create_batch(5, job=job, is_blacklisted=True)
        factories.JobSkillFactory.create_batch(5, job=job, is_blacklisted=False)
        blacklisted_industry_job_skills = factories.IndustryJobSkillFactory.create_batch(
            5, job=job, is_blacklisted=True
        )
        factories.IndustryJobSkillFactory.create_batch(5, job=job, is_blacklisted=False)

        # Assert initial data.
        job_skills, industry_job_skills = job.get_whitelisted_job_skills()
        assert len(job_skills) == 5
        assert len(industry_job_skills) == 5

        # whitelist some of the job skills from JobSkill model.
        skill_ids = [job_skill.skill.id for job_skill in blacklisted_job_skills][:3]
        job.whitelist_job_skills(skill_ids)

        # Make sure there were only 2 queries made to fetch the data, one for job skills
        # and another for industry job skills.
        with self.assertNumQueries(2):
            # Assert database records.
            job_skills, industry_job_skills = job.get_whitelisted_job_skills()
            assert len(job_skills) == 8
            assert len(industry_job_skills) == 5

        # Now whitelist some if the industry job skills.
        skill_ids = [job_skill.skill.id for job_skill in blacklisted_industry_job_skills][:2]
        job.whitelist_job_skills(skill_ids)

        # Make sure there were only 2 queries made to fetch the data, one for job skills
        # and another for industry job skills.
        with self.assertNumQueries(2):
            # Assert database records.
            job_skills, industry_job_skills = job.get_whitelisted_job_skills()
            assert len(job_skills) == 8
            assert len(industry_job_skills) == 7

        # Now whitelist everything.
        skill_ids = [job_skill.skill.id for job_skill in blacklisted_industry_job_skills]
        skill_ids.extend([job_skill.skill.id for job_skill in blacklisted_job_skills])
        job.whitelist_job_skills(skill_ids)

        # Make sure there were only 2 queries made to fetch the data, one for job skills
        # and another for industry job skills.
        with self.assertNumQueries(2):
            # Assert database records.
            job_skills, industry_job_skills = job.get_whitelisted_job_skills()
            assert len(job_skills) == 10
            assert len(industry_job_skills) == 10

        with self.assertNumQueries(2):
            # Assert database records.
            job_skills, industry_job_skills = job.get_blacklisted_job_skills()
            assert len(job_skills) == 0
            assert len(industry_job_skills) == 0

    def test_blacklist_job_skills(self):
        """
        Validate blacklist_job_skills removes skills from the blacklist.
        """
        job = factories.JobFactory.create()
        factories.JobSkillFactory.create_batch(5, job=job, is_blacklisted=True)
        whitelisted_job_skills = factories.JobSkillFactory.create_batch(5, job=job, is_blacklisted=False)
        factories.IndustryJobSkillFactory.create_batch(5, job=job, is_blacklisted=True)
        whitelisted_industry_job_skills = factories.IndustryJobSkillFactory.create_batch(
            5, job=job, is_blacklisted=False
        )

        # Assert initial data.
        job_skills, industry_job_skills = job.get_blacklisted_job_skills()
        assert len(job_skills) == 5
        assert len(industry_job_skills) == 5

        # blacklist some of the job skills from JobSkill model.
        skill_ids = [job_skill.skill.id for job_skill in whitelisted_job_skills][:3]
        job.blacklist_job_skills(skill_ids)

        # Make sure there were only 2 queries made to fetch the data, one for job skills
        # and another for industry job skills.
        with self.assertNumQueries(2):
            # Assert database records.
            job_skills, industry_job_skills = job.get_blacklisted_job_skills()
            assert len(job_skills) == 8
            assert len(industry_job_skills) == 5

        # Now whitelist some if the industry job skills.
        skill_ids = [job_skill.skill.id for job_skill in whitelisted_industry_job_skills][:2]
        job.blacklist_job_skills(skill_ids)

        # Make sure there were only 2 queries made to fetch the data, one for job skills
        # and another for industry job skills.
        with self.assertNumQueries(2):
            # Assert database records.
            job_skills, industry_job_skills = job.get_blacklisted_job_skills()
            assert len(job_skills) == 8
            assert len(industry_job_skills) == 7

        # Now whitelist everything.
        skill_ids = [job_skill.skill.id for job_skill in whitelisted_industry_job_skills]
        skill_ids.extend([job_skill.skill.id for job_skill in whitelisted_job_skills])
        job.blacklist_job_skills(skill_ids)

        # Make sure there were only 2 queries made to fetch the data, one for job skills
        # and another for industry job skills.
        with self.assertNumQueries(2):
            # Assert database records.
            job_skills, industry_job_skills = job.get_blacklisted_job_skills()
            assert len(job_skills) == 10
            assert len(industry_job_skills) == 10

        with self.assertNumQueries(2):
            # Assert database records.
            job_skills, industry_job_skills = job.get_whitelisted_job_skills()
            assert len(job_skills) == 0
            assert len(industry_job_skills) == 0


@mark.django_db
class TestJobPath(TestCase):
    """
    Tests for the ``JobPath`` model.
    """

    def test_string_representation(self):
        """
        Test the string representation of the JobPath model.
        """
        job_path = factories.JobPathFactory()
        expected_str = 'Job path from "{}" to "{}" is "{}")'.format(
            job_path.current_job,
            job_path.future_job,
            job_path.description
        )
        expected_repr = 'JobPath(current_job="{}", future_job="{}", description="{}")'.format(
            job_path.current_job,
            job_path.future_job,
            job_path.description
        )

        assert expected_str == job_path.__str__()
        assert expected_repr == job_path.__repr__()

    def test_current_and_future_should_be_different(self):
        """
        Verify that correct exception has raised if current and future job are same.
        """
        job = factories.JobFactory()
        with pytest.raises(ValidationError) as raised_exception:
            factories.JobPathFactory(current_job=job, future_job=job)

        assert raised_exception.value.args[0]['__all__'][0].message == 'Current and Future jobs can not be same.'

    def test_unique_together(self):
        """
        Verify that unique_together constraint works as expected.
        """
        current_job = factories.JobFactory(external_id='1111')
        future_job = factories.JobFactory(external_id='2222')
        with pytest.raises(ValidationError) as raised_exception:
            factories.JobPathFactory(current_job=current_job, future_job=future_job)
            factories.JobPathFactory(current_job=current_job, future_job=future_job)

        error_message = 'Job Path Description with this Current job and Future job already exists.'
        assert raised_exception.value.messages[0] == error_message


@mark.django_db
class TestSkillSubCategoryFactory(TestCase):
    """
    Tests for the ``SkillSubCategory`` model.
    """

    def test_string_representation(self):
        """
        Test the string representation of the Job model.
        """
        skill_sub_category = factories.SkillSubCategoryFactory()
        expected_str = '<SkillSubCategory id="{}" name="{}" category="{}">'.format(
            skill_sub_category.id, skill_sub_category.name, skill_sub_category.category.name
        )
        expected_repr = '<SkillSubCategory id="{}" name="{}">'.format(skill_sub_category.id, skill_sub_category.name)

        assert expected_str == skill_sub_category.__str__()
        assert expected_repr == skill_sub_category.__repr__()


@mark.django_db
class TestSkillsQuiz(TestCase):
    """
    Tests for the ``SkillsQuiz`` model.
    """

    def test_string_representation(self):
        """
        Test the string representation of the SkillsQuiz model.
        """
        skill_quiz = factories.SkillsQuizFactory()
        expected_str = '<SkillsQuiz id="{}" user="{}">'.format(
            skill_quiz.id, skill_quiz.username
        )
        expected_repr = '<SkillsQuiz id="{}" user="{}">'.format(skill_quiz.id, skill_quiz.username)

        assert expected_str == skill_quiz.__str__()
        assert expected_repr == skill_quiz.__repr__()


@mark.django_db
class TestIndustry(TestCase):
    """
    Tests for the ``Industry`` model.
    """

    def test_string_representation(self):
        """
        Test the string representation of the SkillsQuiz model.
        """
        # We do need to create industry as it is pre-populated by the data migration.
        industry = Industry.objects.first()
        expected_str = '<Industry id="{}" name="{}">'.format(industry.id, industry.name)
        expected_repr = '<Industry id="{}" code="{}">'.format(industry.id, industry.code)

        assert expected_str == industry.__str__()
        assert expected_repr == industry.__repr__()


@mark.django_db
class TestB2CJobAllowlist(TestCase):
    """
    Tests for the ``B2CJobAllowList`` model.
    """

    def test_string_representation(self):
        """
        Test the string representation of the B2CJobAllowList model.
        """
        allowlisted_job = factories.JobFactory.create(external_id="ET123456789", name="AllowlistTestJob")
        factories.B2CJobAllowlistFactory.create(job=allowlisted_job)
        allowList_entry = B2CJobAllowList.objects.first()
        expected_str = '<External Id = "{}" Job ="{}">'.format(allowList_entry.job.external_id, allowList_entry.job)
        expected_repr = '<External Id = "{}" Job ="{}">'.format(allowList_entry.job.external_id, allowList_entry.job)

        assert expected_str == allowList_entry.__str__()
        assert expected_repr == allowList_entry.__repr__()


@mark.django_db
class SkillValidationConfigurationTests(TestCase):
    """
    Tests for the ``SkillValidationConfiguration`` model.
    """
    def setUp(self):
        super().setUp()

        self.mock_course_run = MockCourseRun(course_key='RichX+GoldX', course_run_key='course-v1:RichX+GoldX+1T2024')
        self.courses = [MockCourse() for _ in range(3)]
        self.courses[0].key = self.mock_course_run.course_key
        self.provider_patcher = patch('taxonomy.models.get_course_metadata_provider')
        self.mock_provider = self.provider_patcher.start()
        self.mock_provider.return_value = DiscoveryCourseMetadataProvider(self.courses)

    def tearDown(self):
        super().tearDown()

        self.provider_patcher.stop()

    def test_model_obj_creation_with_course_and_org(self):
        """
        Verify that an `ValidationError` is raised if user try to create a
        SkillValidationConfiguration with both course and organization.
        """
        with pytest.raises(ValidationError) as raised_exception:
            factories.SkillValidationConfigurationFactory(
                course_key=self.courses[0].key,
                organization=self.courses[0].key.split('+')[0]
            )

        assert raised_exception.value.message_dict['__all__'][0] == 'Add either course key or organization.'

    def test_model_obj_creation_with_wrong_course_key(self):
        """
        Verify that a `ValidationError` is raised if user try to create a
        SkillValidationConfiguration with incorrect course key.
        """
        with pytest.raises(ValidationError) as raised_exception:
            factories.SkillValidationConfigurationFactory(course_key='MAx+WoWx')

        assert raised_exception.value.message_dict == {'course_key': ['Course with key MAx+WoWx does not exist.']}

    def test_model_obj_creation_with_wrong_org_key(self):
        """
        Verify that a `ValidationError` is raised if user try to create a
        SkillValidationConfiguration with incorrect organization key.
        """
        with pytest.raises(ValidationError) as raised_exception:
            factories.SkillValidationConfigurationFactory(organization='MAx')

        assert raised_exception.value.message_dict == {'organization': ['Organization with key MAx does not exist.']}

    def test_model_is_disabled_with_course_key(self):
        """
        Verify that a `is_disabled` work as expected if a skill validation is disabled for a course.
        """
        factories.SkillValidationConfigurationFactory(course_key=self.mock_course_run.course_key)
        assert SkillValidationConfiguration.is_disabled(course_run_key=self.mock_course_run.course_run_key)

    def test_model_is_disabled_with_org_key(self):
        """
        Verify that a `is_disabled` work as expected if a skill validation is disabled for an organization.
        """
        organization = self.courses[0].key.split('+')[0]
        factories.SkillValidationConfigurationFactory(organization=organization)
        assert SkillValidationConfiguration.is_disabled(course_run_key=self.mock_course_run.course_run_key)

    def test_model_is_disabled_with_wrong_course_run_key_format(self):
        """
        Verify that a `is_disabled` work as expected if a course_run_key is in wrong format.
        """
        assert SkillValidationConfiguration.is_disabled(course_run_key='blah blah blah') is False

    def test_model_is_disabled(self):
        """
        Verify that a `is_disabled` work as expected if no condition satisfies.
        """
        assert SkillValidationConfiguration.is_disabled(course_run_key='course-v1:org+course+run') is False

    def test_model_object_str_with_course_key(self):
        """
        Verify that SkillValidationConfiguration model __str__ work as expected for a course key.
        """
        disabled_config = factories.SkillValidationConfigurationFactory(course_key=self.mock_course_run.course_key)
        assert str(disabled_config) == 'Skill validation disabled for course: RichX+GoldX'

    def test_model_object_str_with_org_key(self):
        """
        Verify that SkillValidationConfiguration model __str__ work as expected for an organization key.
        """
        organization = self.courses[0].key.split('+')[0]
        disabled_config = factories.SkillValidationConfigurationFactory(organization=organization)
        assert str(disabled_config) == 'Skill validation disabled for organization: RichX'
