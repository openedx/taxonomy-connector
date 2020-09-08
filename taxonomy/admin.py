# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from taxonomy.models import JobSkills, Job, JobPostings


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(JobSkills)
class JobSkillsAdmin(admin.ModelAdmin):
    list_display = ('name', 'job','significance', 'unique_postings')
    search_fields = ('name', 'significance',)

""""
@admin.register(JobPostings)
class JobPostingsAdmin(admin.ModelAdmin):
    list_display = ['job__name', 'median_salary','median_posting_duration', 'unique_postings', 'unique_companies']
    search_fields = ['job__name']
"""