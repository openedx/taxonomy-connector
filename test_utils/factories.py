# -*- coding: utf-8 -*-
"""
Model Factories for the taxonomy tests.
"""
import factory
from faker import Factory as FakerFactory

from taxonomy.models import BlacklistedCourseSkill, Skill

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
class BlacklistedCourseSkillFactory(factory.django.DjangoModelFactory):
    """
    Factory class for BlacklistedCourseSkill model.
    """

    class Meta:
        """
        Meta for ``BlacklistedCourseSkillFactory``.
        """

        model = BlacklistedCourseSkill
        django_get_or_create = ('course_id', 'skill')

    course_id = factory.LazyAttribute(lambda x: FAKER.slug())
    skill = factory.SubFactory(SkillFactory)
