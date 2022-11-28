# -*- coding: utf-8 -*-
"""
Admin views for the taxonomy service.

Only the models that have administration requirements are exposed via the django admin portal.
"""
from __future__ import unicode_literals

from django.contrib import admin

from taxonomy.models import (
    CourseSkills, Job, JobPostings, JobSkills, ProgramSkill, Skill, Translation, SkillCategory,
    SkillSubCategory, SkillsQuiz, RefreshProgramSkillsConfig, Industry, IndustryJobSkill,
    XBlockSkills, XBlockSkillData
)


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


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    """
    Administrative view for Jobs.
    """

    list_display = ('id', 'name', 'created', 'modified')
    search_fields = ('name',)


@admin.register(JobSkills)
class JobSkillsAdmin(admin.ModelAdmin):
    """
    Administrative view for Job Skills.
    """

    list_display = ('id', 'skill', 'job', 'significance', 'unique_postings', 'created', 'modified')
    search_fields = ('name', 'significance',)


@admin.register(IndustryJobSkill)
class IndustryJobSkillAdmin(admin.ModelAdmin):
    """
    Administrative view for Industry Job Skills.
    """

    list_display = ('id', 'industry', 'skill', 'job', 'significance', 'unique_postings', 'created', 'modified')


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
