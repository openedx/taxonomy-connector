"""
Views for taxonomy-connector app.
"""
from collections import namedtuple

from django.contrib import admin, messages
from django.contrib.auth import get_permission_codename
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import View

from taxonomy.constants import JOB_SKILLS_URL_NAME
from taxonomy.forms import ExcludeSkillsForm
from taxonomy.models import Job

Option = namedtuple('Option', 'id name')


class JobSkillsView(View):
    """
    Job Skills view.

    For displaying job skills of a particular job.
    """

    template = 'admin/taxonomy/job-skills.html'
    form = ExcludeSkillsForm

    class ContextParameters:
        """
        Namespace-style class for custom context parameters.
        """

        JOB_SKILLS = 'job_skills'
        EXCLUDED_JOB_SKILLS = 'excluded_job_skills'

        JOB = 'job'

    @staticmethod
    def _get_admin_context(request, job):
        """
        Build admin context.
        """
        options = job._meta
        codename = get_permission_codename('change', options)
        return {
            'has_change_permission': request.user.has_perm('%s.%s' % (options.app_label, codename)),
            'opts': options
        }

    @staticmethod
    def _get_skill_options(*query_sets):
        """
        Get a list of skill option tuples containing skills id and skill name.

        Arguments:
            query_sets (list<Queryset>): A list of queryset objects of any class inheriting from `BaseJobSkill` model.

        Returns:
             (list<tuple<int, str>>): A named tuple with skills `id` as id and skill `nam`e as name attribute.
        """
        options = set()
        for qs in query_sets:
            for job_skill in qs:
                options.add(Option(job_skill.skill.id, job_skill.skill.name))
        return options

    def _get_view_context(self, job_pk):
        """
        Return the default context parameters.
        """
        job = get_object_or_404(Job, id=job_pk)
        job_skills, industry_job_skills = job.get_whitelisted_job_skills()
        excluded_job_skills, excluded_industry_job_skills = job.get_blacklisted_job_skills()
        return {
            self.ContextParameters.JOB: job,
            self.ContextParameters.JOB_SKILLS: self._get_skill_options(job_skills, industry_job_skills),
            self.ContextParameters.EXCLUDED_JOB_SKILLS: self._get_skill_options(
                excluded_job_skills, excluded_industry_job_skills
            ),
            'title': job.name,
        }

    def _build_context(self, request, job_pk):
        """
        Build admin and view context used by the template.
        """
        context = self._get_view_context(job_pk)
        context.update(admin.site.each_context(request))
        context.update(self._get_admin_context(request, context['job']))
        return context

    def get(self, request, job_pk):
        """
        Handle GET request - renders the template.

        Arguments:
            request (django.http.request.HttpRequest): Request instance
            job_pk (str): Primary key of the job

        Returns:
            django.http.response.HttpResponse: HttpResponse
        """
        context = self._build_context(request, job_pk)
        context['exclude_skills_form'] = self.form(
            context[self.ContextParameters.JOB_SKILLS],
            context[self.ContextParameters.EXCLUDED_JOB_SKILLS],
        )

        return render(request, self.template, context)

    def post(self, request, job_pk):
        """
        Handle POST request - saves excluded/included skills.

        Arguments:
            request (django.http.request.HttpRequest): Request instance
            job_pk (str): Primary key of the job

        Returns:
            django.http.response.HttpResponse: HttpResponse
        """
        job = Job.objects.get(id=job_pk)
        job_skills, industry_job_skills = job.get_whitelisted_job_skills()
        excluded_job_skills, excluded_industry_job_skills = job.get_blacklisted_job_skills()

        form = self.form(
            job_skills=self._get_skill_options(job_skills, industry_job_skills),
            excluded_job_skills=self._get_skill_options(excluded_job_skills, excluded_industry_job_skills),
            data=request.POST
        )
        if form.is_valid():
            if form.cleaned_data['exclude_skills']:
                job.blacklist_job_skills(form.cleaned_data['exclude_skills'])
            if form.cleaned_data['include_skills']:
                job.whitelist_job_skills(form.cleaned_data['include_skills'])

            messages.add_message(
                request=self.request,
                level=messages.SUCCESS,
                message=_('Job skills were updated successfully.'),
            )
        else:
            messages.add_message(
                request=self.request,
                level=messages.ERROR,
                message=_('Job skills could not be updated, please try again or contact support.'),
            )

        return HttpResponseRedirect(
            reverse(f'admin:{JOB_SKILLS_URL_NAME}', args=(job_pk,))
        )
