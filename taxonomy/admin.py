# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from taxonomy.models import JobSkills, Job
# Register your models here.


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(JobSkills)
class JobSkillsAdmin(admin.ModelAdmin):
    list_display = ('name', 'job','significance', 'unique_postings')
    search_fields = ('name', 'significance',)
