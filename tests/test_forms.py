""" Tests for the `taxonomy` Forms module. """

from django.test import TestCase

from taxonomy.forms import RefreshCourseSkillsForm


class RefreshCourseSkillsFormTest(TestCase):
    """
    Tests for RefreshCourseSkillsForm.
    """

    def test_with_valid_course_uuid(self):
        """
        Test happy path with course_uuid
        """
        data = {
            'course_uuid': ' a6f9804d-76e7-4a2f-85d8-46ca1a096f0f',
        }
        form = RefreshCourseSkillsForm(data=data)
        assert form.is_valid()
        self.assertDictEqual(form.errors, {})

    def test_with_invalid_course_uuid(self):
        """
        Test for form errors.
        """
        data = {
            'course_uuid': '',
        }
        form = RefreshCourseSkillsForm(data=data)
        assert not form.is_valid()
        self.assertDictEqual(form.errors, {'course_uuid': ['This field is required.']})
