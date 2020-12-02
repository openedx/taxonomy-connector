# -*- coding: utf-8 -*-
"""
Forms used by the taxonomy service.
"""

from django import forms


class RefreshCourseSkillsForm(forms.Form):
    """
    Form to refresh course skills data, this form will be used to clean, validate data coming from the UI.
    """

    course_uuid = forms.UUIDField(
        label='Course UUID:',
        required=True,
        widget=forms.TextInput(attrs={'class': 'v-text-field'}),
    )
