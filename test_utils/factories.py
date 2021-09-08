# -*- coding: utf-8 -*-
"""
Model Factories for the taxonomy tests.
"""
import factory
from faker import Factory as FakerFactory

from taxonomy.models import CourseSkills, Job, JobPostings, JobSkills, Skill

FAKER = FakerFactory.create()


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
    name = factory.LazyAttribute(lambda x: FAKER.job())


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
