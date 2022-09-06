# -*- coding: utf-8 -*-
"""
Tests for the taxonomy models.
"""

from pytest import mark

from django.test import TestCase

from taxonomy.models import Job, JobPostings, Skill
from test_utils import factories


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

    def test_get_skill_ids_by_name(self):
        """
        Test the ``get_skill_ids_by_name`` Return correct IDs.
        """
        skill_a = factories.SkillFactory()
        skill_b = factories.SkillFactory()
        skill_c = factories.SkillFactory()  # pylint: disable=unused-variable
        skill_ids = Skill.get_skill_ids_by_name([skill_a.name, skill_b.name])
        assert skill_ids == [skill_a.id, skill_b.id]


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
class TestJobSkills(TestCase):
    """
    Tests for the ``JobSkills`` model.
    """

    def test_string_representation(self):
        """
        Test the string representation of the JobSkills model.
        """
        job_skill = factories.JobSkillFactory()
        expected_str = '<JobSkills name="{}" significance="{}" unique_postings="{}">'.format(
            job_skill.skill.name, job_skill.significance, job_skill.unique_postings
        )
        expected_repr = '<JobSkills id="{0}" name="{1}" job="{2!r}">'.format(
            job_skill.id, job_skill.skill.name, job_skill.job,
        )

        assert expected_str == job_skill.__str__()
        assert expected_repr == job_skill.__repr__()


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
        expected_repr = '<Job id="{}" name="{}" external_id="{}" >'.format(job.id, job.name, job.external_id)

        assert expected_str == job.__str__()
        assert expected_repr == job.__repr__()


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
