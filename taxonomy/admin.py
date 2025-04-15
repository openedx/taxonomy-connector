# -*- coding: utf-8 -*-
"""
Admin views for the taxonomy service.

Only the models that have administration requirements are exposed via the django admin portal.
"""
from __future__ import unicode_literals

from django_object_actions import DjangoObjectActions

from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import re_path, reverse

from taxonomy.constants import JOB_SKILLS_URL_NAME
from taxonomy.models import (
    B2CJobAllowList,
    CourseRunXBlockSkillsTracker,
    CourseSkills,
    Industry,
    IndustryJobSkill,
    Job,
    JobPath,
    JobPostings,
    JobSkills,
    ProgramSkill,
    RefreshProgramSkillsConfig,
    Skill,
    SkillCategory,
    SkillsQuiz,
    SkillSubCategory,
    SkillValidationConfiguration,
    Translation,
    XBlockSkillData,
    XBlockSkills,
)
from taxonomy.views import JobSkillsView


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    """
    Administrative view for Skills.
    """

    list_display = ('id', 'external_id', 'name', 'created', 'modified', 'category_name', 'subcategory_name')
    search_fields = ('external_id', 'name', 'category__name', 'subcategory__name')
    list_filter = ('category', 'subcategory', )

    @admin.display(
        description='Skill Category',
    )
    def category_name(self, obj):
        """
        Name of the skill category.
        """
        return obj.category and obj.category.name

    @admin.display(
        description='Skill Subcategory',
    )
    def subcategory_name(self, obj):
        """
        Name of the skill category.
        """
        return obj.subcategory and obj.subcategory.name


@admin.register(SkillCategory)
class SkillCategoryAdmin(admin.ModelAdmin):
    """
    Administrative view for SkillCategory.
    """

    list_display = ('id', 'name', 'created', 'modified')
    search_fields = ('id', 'name')


@admin.register(SkillSubCategory)
class SkillSubCategoryAdmin(admin.ModelAdmin):
    """
    Administrative view for SkillSubCategory.
    """

    list_display = ('id', 'name', 'category', 'created', 'modified')
    search_fields = ('id', 'name', 'category')


@admin.register(CourseSkills)
class CourseSkillsTitleAdmin(admin.ModelAdmin):
    """
    Administrative view for Course Skills.
    """

    list_display = ('id', 'course_key', 'created', 'modified')
    search_fields = ('course_key',)
    autocomplete_fields = ['skill']


@admin.register(Job)
class JobAdmin(DjangoObjectActions, admin.ModelAdmin):
    """
    Administrative view for Jobs.
    """

    list_display = ('id', 'name', 'created', 'modified')
    search_fields = ('name',)
    actions = ('remove_unused_jobs', )
    change_actions = ('job_skills', )

    @admin.action(
        description="view job skills"
    )
    def job_skills(self, request, obj):
        """
        Object tool handler method - redirects to "Course Skills" view.
        """
        # url names coming from get_urls are prefixed with 'admin' namespace
        return HttpResponseRedirect(
            redirect_to=reverse(f"admin:{JOB_SKILLS_URL_NAME}", args=(obj.pk,)),
        )

    def get_urls(self):
        """
        Return the additional urls used by the custom object tools.
        """
        additional_urls = [
            re_path(
                r"^([^/]+)/skills$",
                self.admin_site.admin_view(JobSkillsView.as_view()),
                name=JOB_SKILLS_URL_NAME,
            ),
        ]
        return additional_urls + super().get_urls()

    job_skills.label = "view job skills"

    @admin.action(
        description='Remove Jobs that are not used anywhere'
    )
    def remove_unused_jobs(self, request, queryset):  # pylint: disable=unused-argument
        """
        Add an action to remove unused jobs from the database.
        """
        delete_count, _ = Job.objects.filter(jobskills__isnull=True).delete()
        messages.info(request, f'Successfully Deleted {delete_count} jobs.')


@admin.register(JobPath)
class JobPathAdmin(admin.ModelAdmin):
    """
    Administrative view for JobPath model.
    """

    list_display = ('id', 'created', 'current_job', 'future_job')
    search_fields = ('current_job__name', 'future_job__name',)


@admin.register(JobSkills)
class JobSkillsAdmin(admin.ModelAdmin):
    """
    Administrative view for Job Skills.
    """

    list_display = ('id', 'is_blacklisted', 'skill', 'job', 'significance', 'unique_postings', 'created', 'modified')
    search_fields = ('name', 'significance',)
    list_filter = ('is_blacklisted', )


@admin.register(IndustryJobSkill)
class IndustryJobSkillAdmin(admin.ModelAdmin):
    """
    Administrative view for Industry Job Skills.
    """

    list_display = (
        'id', 'is_blacklisted', 'industry', 'skill', 'job', 'significance', 'unique_postings', 'created', 'modified',
    )
    list_filter = ('is_blacklisted', )


@admin.register(JobPostings)
class JobPostingsAdmin(admin.ModelAdmin):
    """
    Administrative view for Job Postings.
    """

    list_display = ('median_salary', 'median_posting_duration', 'unique_postings', 'unique_companies',)
    search_fields = ('job__name',)


@admin.register(Translation)
class TranslationAdmin(admin.ModelAdmin):
    """
    Administrative view for Translation.
    """

    list_display = ('id', 'source_model_name', 'source_record_identifier', 'source_model_field',)
    search_fields = ('source_record_identifier',)


@admin.register(SkillsQuiz)
class SkillsQuizAdmin(admin.ModelAdmin):
    """
    Administrative view for Skills Quiz.
    """

    list_display = ('id', 'username', 'current_job',)
    search_fields = ('username',)


@admin.register(ProgramSkill)
class ProgramSkillAdmin(admin.ModelAdmin):
    """
    Admin view for ProgramSkill model.
    """

    list_display = ('program_uuid', 'skill', 'created', 'modified', 'is_blacklisted')
    search_fields = ('program_uuid', 'skill__name')


@admin.register(RefreshProgramSkillsConfig)
class RefreshProgramSkillsConfigAdmin(admin.ModelAdmin):
    """
    RefreshProgramSkillsConfig admin view.
    """


@admin.register(Industry)
class IndustryAdmin(admin.ModelAdmin):
    """
    Industry admin view.
    """

    list_display = ('id', 'code', 'name',)
    search_fields = ('name', )
    list_filter = ('name', )


@admin.register(XBlockSkills)
class XBlockSkillsAdmin(admin.ModelAdmin):
    """
    Admin view for XBlockSkills model.
    """

    list_display = ('usage_key', 'requires_verification', 'auto_processed', 'created', 'modified')
    search_fields = ('usage_key',)


@admin.register(XBlockSkillData)
class XBlockSkillDataAdmin(admin.ModelAdmin):
    """
    Admin view for XBlockSkillData model.
    """

    list_display = ('xblock', 'skill', 'verified_count', 'verified', 'created', 'modified', 'is_blacklisted')
    search_fields = ('skill__name',)


@admin.register(CourseRunXBlockSkillsTracker)
class CourseRunXBlockSkillsTrackeAdmin(admin.ModelAdmin):
    """
    Admin view for CourseRunXBlockSkillsTracker model.
    """

    list_display = ('course_run_key',)
    search_fields = ('course_run_key',)


@admin.register(B2CJobAllowList)
class B2CJobAllowListAdmin(admin.ModelAdmin):
    """
    Admin model for B2C Job Allow list.
    """

    list_display = ('id', 'external_id', 'job_name',)
    search_fields = ('job__name', 'job__external_id',)
    autocomplete_fields = ('job',)

    @admin.display(
        description='External ID',
    )
    def external_id(self, obj):
        """
        External Id of the related job.
        """
        return obj.job.external_id

    @admin.display(
        description='Job Name',
    )
    def job_name(self, obj):
        """
        Name of the related job.
        """
        return obj.job.name


@admin.register(SkillValidationConfiguration)
class SkillValidationConfiguratonAdmin(admin.ModelAdmin):
    """
    Admin view for SkillValidationConfiguration model.
    """
