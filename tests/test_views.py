"""
Tests for the `taxonomy` views module.
"""
import mock

from django.contrib import messages
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase

from taxonomy.views import RefreshCourseSkills
from test_utils.mocks import MockCourse
from test_utils.providers import DiscoveryCourseMetadataProvider
from test_utils.sample_responses.skills import SKILLS_EMSI_CLIENT_RESPONSE


class RefreshCourseSkillsTest(TestCase):
    """
    Functional Tests for RefreshCourseSkills Page.
    """

    def setUp(self):
        # Every test needs access to the request factory.
        super().setUp()
        self.request = RequestFactory().post('/')
        self.user = User.objects.create_user(
            username="edx",
            is_staff=True, is_superuser=True
        )

    def test_form_set_in_context(self):
        """
        Test that the form is available to html template through context.
        """
        self.request.user = self.user
        view = RefreshCourseSkills()
        view.setup(self.request)

        context = view.get_context_data()
        self.assertIn('course_uuid', context['form'].fields)

    def test_raise_permission_denied_for_non_staff_user(self):
        """
        Test that the only staff and admin user has access to this view.
        """
        user = self.user
        user.is_staff = False
        self.request.user = user
        view = RefreshCourseSkills()
        view.setup(self.request)
        with self.assertRaises(PermissionDenied):
            view.get_context_data()

    def test_raise_permission_denied_for_anonymous_user(self):
        """
        Test the validation for anonymous users.
        """
        user = AnonymousUser()
        self.request.user = user
        view = RefreshCourseSkills()
        view.setup(self.request)
        with self.assertRaises(PermissionDenied):
            view.get_context_data()

    @mock.patch('taxonomy.views.RefreshCourseSkills._update_course_skills')
    @mock.patch('taxonomy.views.render')
    def test_form_post(self, get_course_skills_mock, mock_render):
        """
        Test the data in form on post request.
        """
        request = self.request
        course_uuid = 'a6f9804d-76e7-4a2f-85d8-46ca1a096f0f'
        request.user = self.user
        get_course_skills_mock.return_value = {}
        request.POST = {'course_uuid': course_uuid}
        view = RefreshCourseSkills()
        view.setup(request)
        view.post(request)
        self.assertIn(course_uuid, mock_render.call_args[0][0].urn)

    @mock.patch('taxonomy.views.RefreshCourseSkills._update_course_skills')
    @mock.patch('taxonomy.views.render')
    def test_form_post_empty_data(self, get_course_skills_mock, mock_render):
        """
        Test the empty data in form on post request.
        """
        request = self.request
        course_uuid = ''
        request.user = self.user
        get_course_skills_mock.return_value = {}
        request.POST = {'course_uuid': course_uuid}
        view = RefreshCourseSkills()
        view.setup(request)
        view.post(request)
        self.assertEqual(mock_render.call_args, None)

    @mock.patch('taxonomy.management.commands.refresh_course_skills.utils.get_course_metadata_provider')
    @mock.patch('taxonomy.management.commands.refresh_course_skills.utils.EMSISkillsApiClient.get_course_skills')
    def test_update_course_skill(self, get_course_skills_mock, get_course_provider_mock):
        """
        Test that the course skills are updated on passing valid course uuid.
        """
        request = self.request
        # Annotate a request object with a session
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()

        # Annotate a request object with a messages
        middleware = MessageMiddleware()
        middleware.process_request(request)
        request.session.save()

        get_course_skills_mock.return_value = SKILLS_EMSI_CLIENT_RESPONSE
        course = MockCourse()
        get_course_provider_mock.return_value = DiscoveryCourseMetadataProvider([course])
        request.user = self.user
        view = RefreshCourseSkills()
        view.setup(request)
        view._update_course_skills(course.uuid)  # pylint: disable=protected-access

        msg = ('Skills data for course_key: {} is updated.'.format(course.uuid))
        msg_tag = 'success'
        storage = messages.get_messages(request)
        for message in storage:
            self.assertEqual(msg, message.message)
            self.assertEqual(msg_tag, message.tags)

    @mock.patch('taxonomy.management.commands.refresh_course_skills.utils.get_course_metadata_provider')
    def test_update_course_skill_failed(self, get_course_provider_mock):
        """
        Test that the course skills updation failed and exception is raised.
        """
        request = self.request

        # Annotate a request object with a session
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()

        # Annotate a request object with a messages
        middleware = MessageMiddleware()
        middleware.process_request(request)
        request.session.save()
        msg = 'Exception with Taxonomy Service.'

        get_course_provider_mock.side_effect = Exception(msg)

        request.user = self.user
        view = RefreshCourseSkills()
        view.setup(request)

        view._update_course_skills("uuid")  # pylint: disable=protected-access
        msg_tag = 'error'
        storage = messages.get_messages(request)
        for message in storage:
            self.assertIn(msg, message.message.args)
            self.assertEqual(msg_tag, message.tags)

    @mock.patch('taxonomy.management.commands.refresh_course_skills.utils.get_course_metadata_provider')
    @mock.patch('taxonomy.management.commands.refresh_course_skills.utils.EMSISkillsApiClient.get_course_skills')
    def test_update_course_skill_failed_unknown_uuid(self, get_course_skills_mock, get_course_provider_mock):
        """
        Test that the course skills updation failed on passing
         invalid or empty course uuid and command error is raised.
        """
        request = self.request

        # Annotate a request object with a session
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()

        # Annotate a request object with a messages
        middleware = MessageMiddleware()
        middleware.process_request(request)
        request.session.save()

        get_course_provider_mock.return_value = DiscoveryCourseMetadataProvider([])
        get_course_skills_mock.return_value = SKILLS_EMSI_CLIENT_RESPONSE
        request.user = self.user
        view = RefreshCourseSkills()
        view.setup(request)

        view._update_course_skills("uuid")  # pylint: disable=protected-access
        msg = "No course metadata was found for following courses. ['uuid']"
        msg_tag = 'error'
        storage = messages.get_messages(request)
        for message in storage:
            self.assertIn(msg, message.message.args)
            self.assertEqual(msg_tag, message.tags)
