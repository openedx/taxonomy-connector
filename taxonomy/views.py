# -*- coding: utf-8 -*-
"""
Django views for taxonomy application.
"""
from django.contrib import messages
from django.core import management
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.views.generic import TemplateView

from taxonomy.forms import RefreshCourseSkillsForm


class RefreshCourseSkills(TemplateView):
    """
    Create/Update Course Skills View.
    """

    template_name = "taxonomy/refresh_course_skills.html"

    def get_context_data(self, **kwargs):
        """
        Return the context data needed to render the view.
        """
        if self.request.user.is_authenticated and self.request.user.is_staff:
            context = super().get_context_data(**kwargs)
            context.update({
                'form': RefreshCourseSkillsForm(),
            })
            return context
        raise PermissionDenied()

    def post(self, request):
        """
        Process the post request by creating an instance of course skills after cleaning and validating post data.
        """
        form = RefreshCourseSkillsForm(request.POST)
        if form.is_valid():
            course_uuid = form.cleaned_data['course_uuid']
            self._update_course_skills(course_uuid)
        return render(request, self.template_name, {"form": form})

    def _update_course_skills(self, course_uuid):
        """
        Call the management command to refresh data.
        """
        try:
            management.call_command('refresh_course_skills', '--course', course_uuid, '--commit')
            message = ('Skills data for course_key: {} is updated.'.format(course_uuid))
            messages.add_message(self.request, messages.SUCCESS, message)
        except Exception as error:  # pylint: disable=broad-except
            messages.add_message(self.request, messages.ERROR, error)
