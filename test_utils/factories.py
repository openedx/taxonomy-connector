# -*- coding: utf-8 -*-
"""
Model Factories for the taxonomy tests.
"""
import factory
from faker import Factory as FakerFactory
from faker import Faker

from taxonomy.models import (
    CourseSkills, Job, JobPostings, JobSkills, Skill, Translation, SkillCategory, SkillSubCategory,
)

FAKER = FakerFactory.create()
FAKER_OBJECT = Faker()


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
    name = factory.LazyAttribute(lambda x: FAKER.job())
    info_url = factory.LazyAttribute(lambda x: FAKER.uri())
    type_id = factory.LazyAttribute(lambda x: FAKER.slug())
    type_name = factory.LazyAttribute(lambda x: FAKER.text(max_nb_chars=20))
    description = factory.LazyAttribute(lambda x: FAKER.text(max_nb_chars=200))
    category = factory.SubFactory(SkillCategoryFactory)
    subcategory = factory.SubFactory(SkillSubCategoryFactory)


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


class JobFactory(factory.django.DjangoModelFactory):
    """
        Factory class for Job model.
    """

    class Meta:

        model = Job

    external_id = factory.Sequence('JOB-{}'.format)
    name = factory.LazyAttribute(lambda x: FAKER_OBJECT.unique.job())


class JobSkillFactory(factory.django.DjangoModelFactory):
    """
    Factory class for JobSkills model.
    """

    class Meta:
        model = JobSkills
        django_get_or_create = ('job', 'skill')

    skill = factory.SubFactory(SkillFactory)
    job = factory.SubFactory(JobFactory)
    significance = factory.LazyAttribute(lambda x: FAKER.pyfloat(min_value=0, max_value=100))
    unique_postings = factory.LazyAttribute(lambda x: FAKER.pyfloat(min_value=0, max_value=100000000))


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
