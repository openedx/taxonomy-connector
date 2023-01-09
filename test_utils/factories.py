# -*- coding: utf-8 -*-
"""
Model Factories for the taxonomy tests.
"""
import random
from uuid import uuid4

import factory
from faker import Factory as FakerFactory
from faker import Faker

from taxonomy.models import (
    CourseSkills, Job, JobPostings, JobSkills, Skill, Translation, SkillCategory, SkillSubCategory, ProgramSkill,
    SkillsQuiz, RefreshCourseSkillsConfig, RefreshProgramSkillsConfig, Industry, IndustryJobSkill,
    XBlockSkillData, XBlockSkills
)
from taxonomy.choices import UserGoal

FAKER = FakerFactory.create()
FAKER_OBJECT = Faker()


# pylint: disable=no-member, invalid-name
class RefreshProgramSkillsConfigFactory(factory.django.DjangoModelFactory):
    """
    Factory class for RefreshProgramSkillsConfig model.
    """

    class Meta:
        """
        Meta for ``RefreshProgramSkillsConfig``.
        """

        model = RefreshProgramSkillsConfig
        django_get_or_create = ('id',)

    id = factory.Sequence(lambda n: n)
    arguments = factory.LazyAttribute(lambda x: FAKER.word())


# pylint: disable=no-member, invalid-name
class RefreshCourseSkillsConfigFactory(factory.django.DjangoModelFactory):
    """
    Factory class for RefreshCourseSkillsConfig model.
    """

    class Meta:
        """
        Meta for ``RefreshCourseSkillsConfig``.
        """

        model = RefreshCourseSkillsConfig
        django_get_or_create = ('id',)

    id = factory.Sequence(lambda n: n)
    arguments = factory.LazyAttribute(lambda x: FAKER.word())


# pylint: disable=no-member, invalid-name
class SkillCategoryFactory(factory.django.DjangoModelFactory):
    """
    Factory class for SkillCategory model.
    """

    class Meta:
        """
        Meta for ``SkillCategory``.
        """

        model = SkillCategory
        django_get_or_create = ('id',)

    id = factory.Sequence(lambda n: n)
    name = factory.LazyAttribute(lambda x: FAKER.word())


# pylint: disable=no-member, invalid-name
class SkillSubCategoryFactory(factory.django.DjangoModelFactory):
    """
    Factory class for SkillSubCategory model.
    """

    class Meta:
        """
        Meta for ``SkillSubCategory``.
        """

        model = SkillSubCategory
        django_get_or_create = ('id',)

    id = factory.Sequence(lambda n: n)
    name = factory.LazyAttribute(lambda x: FAKER.word())
    category = factory.SubFactory(SkillCategoryFactory)


# pylint: disable=no-member
class SkillFactory(factory.django.DjangoModelFactory):
    """
    Factory class for Skill model.
    """

    class Meta:
        """
        Meta for ``SkillFactory``.
        """

        model = Skill
        django_get_or_create = ('external_id', )

    external_id = factory.Sequence('SKILL-{}'.format)
    name = factory.Sequence('SKILL-{}'.format)
    info_url = factory.LazyAttribute(lambda x: FAKER.uri())
    type_id = factory.LazyAttribute(lambda x: FAKER.slug())
    type_name = factory.LazyAttribute(lambda x: FAKER.text(max_nb_chars=20))
    description = factory.LazyAttribute(lambda x: FAKER.text(max_nb_chars=200))
    category = factory.SubFactory(SkillCategoryFactory)
    subcategory = factory.SubFactory(SkillSubCategoryFactory)


# pylint: disable=no-member
class XBlockSkillsFactory(factory.django.DjangoModelFactory):
    """
    Factory class for XBlockSkills model.
    """

    class Meta:
        """
        Meta for ``XBlockSkillsFactory``.
        """

        model = XBlockSkills
        django_get_or_create = ('usage_key',)

    usage_key = factory.LazyAttribute(
        lambda x: "%(key)s-v1:edx+%(key)s+%(key)s+%(key)s@%(key)s" % {"key": FAKER.slug()},
    )


# pylint: disable=no-member
class XBlockSkillDataFactory(factory.django.DjangoModelFactory):
    """
    Factory class for XBlockSkills model.
    """

    class Meta:
        """
        Meta for ``XBlockSkillsFactory``.
        """

        model = XBlockSkillData
        django_get_or_create = ('xblock', 'skill')

    skill = factory.SubFactory(SkillFactory)
    xblock = factory.SubFactory(XBlockSkillsFactory)
    confidence = factory.LazyAttribute(lambda x: FAKER.pyfloat(min_value=0, max_value=1))
    is_blacklisted = False


# pylint: disable=no-member
class CourseSkillsFactory(factory.django.DjangoModelFactory):
    """
    Factory class for CourseSkills model.
    """

    class Meta:
        """
        Meta for ``CourseSkillsFactory``.
        """

        model = CourseSkills
        django_get_or_create = ('course_key', 'skill')

    course_key = factory.LazyAttribute(lambda x: FAKER.slug())
    skill = factory.SubFactory(SkillFactory)
    confidence = factory.LazyAttribute(lambda x: FAKER.pyfloat(min_value=0, max_value=1))
    is_blacklisted = False


class ProgramSkillFactory(factory.django.DjangoModelFactory):
    """
    Factory class for ProgramSkill model.
    """

    class Meta:
        """
        Meta for ``ProgramSkillFactory``.
        """

        model = ProgramSkill
        django_get_or_create = ('program_uuid', 'skill')

    program_uuid = factory.LazyFunction(uuid4)
    skill = factory.SubFactory(SkillFactory)
    confidence = factory.LazyAttribute(lambda x: FAKER.pyfloat(min_value=0, max_value=1))
    is_blacklisted = False


class JobFactory(factory.django.DjangoModelFactory):
    """
        Factory class for Job model.
    """

    class Meta:

        model = Job

    external_id = factory.Sequence('JOB-{}'.format)
    name = factory.LazyAttribute(lambda x: FAKER_OBJECT.unique.job())


class IndustryFactory(factory.django.DjangoModelFactory):
    """
    Factory class for Industry model.
    """

    class Meta:
        model = Industry
        django_get_or_create = ('code',)

    code = factory.Sequence(lambda n: n)
    name = factory.LazyAttribute(lambda x: FAKER.word())


class JobSkillFactory(factory.django.DjangoModelFactory):
    """
    Factory class for JobSkills model.
    """

    class Meta:
        model = JobSkills
        django_get_or_create = ('job', 'skill')

    skill = factory.SubFactory(SkillFactory)
    job = factory.SubFactory(JobFactory)
    significance = factory.LazyAttribute(lambda x: FAKER.pyfloat(right_digits=2, min_value=0, max_value=100))
    unique_postings = factory.LazyAttribute(lambda x: FAKER.pyint(min_value=0, max_value=100000000))


class IndustryJobSkillFactory(factory.django.DjangoModelFactory):
    """
    Factory class for IndustryJobSkill model.
    """

    class Meta:
        model = IndustryJobSkill
        django_get_or_create = ('industry', 'job', 'skill')
    industry = factory.SubFactory(IndustryFactory)
    skill = factory.SubFactory(SkillFactory)
    job = factory.SubFactory(JobFactory)
    significance = factory.LazyAttribute(lambda x: FAKER.pyfloat(right_digits=2, min_value=0, max_value=100))
    unique_postings = factory.LazyAttribute(lambda x: FAKER.pyint(min_value=0, max_value=100000000))


class JobPostingsFactory(factory.django.DjangoModelFactory):
    """
    Factory class fofr JobPostings
    """

    class Meta:
        model = JobPostings
        django_get_or_create = ('job',)

    job = factory.SubFactory(JobFactory)
    median_salary = factory.LazyAttribute(lambda x: FAKER.pyfloat(min_value=0, max_value=100))
    median_posting_duration = factory.LazyAttribute(lambda x: FAKER.pyint(min_value=0, max_value=100000000))
    unique_postings = factory.LazyAttribute(lambda x: FAKER.pyint(min_value=0, max_value=100000000))
    unique_companies = factory.LazyAttribute(lambda x: FAKER.pyint(min_value=0, max_value=100000000))


class TranslationFactory(factory.django.DjangoModelFactory):
    """
    Factory class for Translation model.
    """

    class Meta:
        """
        Meta for ``Translation``.
        """

        model = Translation
        django_get_or_create = ('source_record_identifier',)

    source_record_identifier = factory.LazyAttribute(lambda x: FAKER.slug())
    source_model_name = factory.LazyAttribute(lambda x: FAKER.word())
    source_model_field = factory.LazyAttribute(lambda x: FAKER.word())
    source_text = factory.LazyAttribute(lambda x: FAKER.text(max_nb_chars=200))
    source_language = factory.LazyAttribute(lambda x: FAKER.language_code())
    translated_text = factory.LazyAttribute(lambda x: FAKER.text(max_nb_chars=200))
    translated_text_language = factory.LazyAttribute(lambda x: FAKER.language_code())


class SkillsQuizFactory(factory.django.DjangoModelFactory):
    """
    Factory class for SkillsQuiz model.
    """
    class Meta:
        model = SkillsQuiz

    username = factory.Sequence(lambda n: 'user_%d' % n)
    current_job = factory.SubFactory(JobFactory)
    goal = factory.LazyFunction(lambda: random.choice(UserGoal.choices)[0])

    @factory.post_generation
    def skills(self, create, extracted, **kwargs):  # pylint: disable=unused-argument
        """
        Post generation hook to add skills to skills quiz model instance.
        """
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            for skill in extracted:
                self.skills.add(skill)
        else:
            self.skills.add(SkillFactory.create())

    @factory.post_generation
    def future_jobs(self, create, extracted, **kwargs):  # pylint: disable=unused-argument
        """
        Post generation hook to add future jobs to skills quiz model instance.
        """
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            for future_job in extracted:
                self.future_jobs.add(future_job)
        else:
            self.future_jobs.add(JobFactory.create())
