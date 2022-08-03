"""
Test that there are no errors in validators logic.

These tests are here to validate that errors will not appear while running
validation logic inside host platform.
"""
from taxonomy.validators import CourseMetadataProviderValidator, ProgramProviderValidator
from test_utils.mocks import MockCourse, MockProgram
from test_utils.testcase import TaxonomyTestCase


class TestCourseMetadataProviderValidator(TaxonomyTestCase):
    """
    Validate that validation logic does not have any errors.
    """

    def setUp(self):
        """
        Instantiate an instance of CourseMetadataProviderValidator for use inside tests.
        """
        super(TestCourseMetadataProviderValidator, self).setUp()
        self.course = MockCourse()

        self.course_metadata_validator = CourseMetadataProviderValidator(
            [str(self.course.uuid)]
        )

    def test_validate(self):
        """
        Validate that code runs without any errors.
        """
        self.course_metadata_validator.validate()


class TestProgramProviderValidator(TaxonomyTestCase):
    """
    Validate that validation logic does not have any errors.
    """

    def setUp(self):
        """
        Instantiate an instance of ProgramProviderValidator for use inside tests.
        """
        super(TestProgramProviderValidator, self).setUp()
        self.program = MockProgram()

        self.program_validator = ProgramProviderValidator(
            [str(self.program.uuid)]
        )

    def test_validate(self):
        """
        Validate that code runs without any errors.
        """
        self.program_validator.validate()
