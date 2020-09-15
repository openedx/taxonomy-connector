"""Taxonomy Forms."""
from django import forms


class RefreshCourseSkillsForm(forms.Form):
    """Form for the RefreshCourseSkills admin."""

    course_uuid = forms.UUIDField(label='Course UUID:', required=True,
                                  widget=forms.TextInput(attrs={'class': 'v-text-field'}))
