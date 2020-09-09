"""
Mocks for taxonomy tests.
"""
from uuid import uuid4

from mock import MagicMock
from faker import Faker

FAKER = Faker()
DEFAULT = object()


class MockCourse(MagicMock):
    """
    Mock object for course.
    """
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
