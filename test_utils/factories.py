# -*- coding: utf-8 -*-
"""
Model Factories for the taxonomy tests.
"""
import factory
from faker import Factory as FakerFactory

from taxonomy.models import CourseSkills, Skill

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

    external_id = factory.LazyAttribute(lambda x: FAKER.slug())
    name = factory.LazyAttribute(lambda x: FAKER.job())
    info_url = factory.LazyAttribute(lambda x: FAKER.uri())
    type_id = factory.LazyAttribute(lambda x: FAKER.slug())
    type_name = factory.LazyAttribute(lambda x: FAKER.text(max_nb_chars=20))


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
        django_get_or_create = ('course_id', 'skill')

    course_id = factory.LazyAttribute(lambda x: FAKER.slug())
    skill = factory.SubFactory(SkillFactory)
    confidence = factory.LazyAttribute(lambda x: FAKER.pyfloat(min_value=0, max_value=1))
    is_blacklisted = False
