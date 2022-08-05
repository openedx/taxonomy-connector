# -*- coding: utf-8 -*-

"""
Mocks for taxonomy tests.
"""
from uuid import uuid4

from faker import Faker
from mock import MagicMock

FAKER = Faker()
DEFAULT = object()


class MockCourse(MagicMock):
    """
    Mock object for course.
    """
    # pylint: disable=keyword-arg-before-vararg
    def __init__(
            self, uuid=DEFAULT, key=DEFAULT, title=DEFAULT, short_description=DEFAULT, full_description=DEFAULT,
            *args, **kwargs
    ):
        """
        Initialize course related attributes.
        """
        super(MockCourse, self).__init__(*args, **kwargs)

        self.uuid = uuid if uuid is not DEFAULT else uuid4()
        self.key = key if key is not DEFAULT else 'course-id/{}'.format(FAKER.slug())
        self.title = title if title is not DEFAULT else 'Test Course {}'.format(FAKER.sentence())
        self.short_description = short_description if short_description is not DEFAULT else FAKER.sentence(nb_words=10)
        self.full_description = full_description if full_description is not DEFAULT else FAKER.sentence(nb_words=50)


class MockProgram(MagicMock):
    """
    Mock object for program.
    """
    # pylint: disable=keyword-arg-before-vararg
    def __init__(
            self, uuid=DEFAULT, title=DEFAULT, subtitle=DEFAULT, overview=DEFAULT, *args, **kwargs
    ):
        """
        Initialize program related attributes.
        """
        super(MockProgram, self).__init__(*args, **kwargs)

        self.uuid = uuid if uuid is not DEFAULT else uuid4()
        self.title = title if title is not DEFAULT else 'Test Program {}'.format(FAKER.sentence())
        self.subtitle = subtitle if subtitle is not DEFAULT else 'Test Program Subtitle {}'.format(FAKER.sentence())
        self.overview = overview if overview is not DEFAULT else FAKER.sentence(nb_words=50)
