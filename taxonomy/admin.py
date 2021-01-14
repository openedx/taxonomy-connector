# -*- coding: utf-8 -*-
"""
Admin views for the taxonomy service.

Only the models that have administration requirements are exposed via the django admin portal.
"""
from __future__ import unicode_literals

from django.contrib import admin

from taxonomy.models import CourseSkills, Job, JobPostings, JobSkills, Skill


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    """
    Administrative view for Skills.
    """

    list_display = ('id', 'external_id', 'name', 'created', 'modified')
    search_fields = ('external_id', 'name')


@admin.register(CourseSkills)
class CourseSkillsTitleAdmin(admin.ModelAdmin):
    """
    Administrative view for Course Skills.
    """

    list_display = ('id', 'course_id', 'created', 'modified')
    search_fields = ('course_id',)


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


@admin.register(JobPostings)
class JobPostingsAdmin(admin.ModelAdmin):
    """
    Administrative view for Job Postings.
    """

    list_display = ('median_salary', 'median_posting_duration', 'unique_postings', 'unique_companies',)
    search_fields = ('job__name',)
