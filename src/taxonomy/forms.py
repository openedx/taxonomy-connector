"""
Forms for taxonomy-connector app.
"""

from django import forms


class ExcludeSkillsForm(forms.Form):
    """
    Form to handle excluding skills from course.
    """

    exclude_skills = forms.MultipleChoiceField()
    include_skills = forms.MultipleChoiceField()

    def __init__(
            self, job_skills, excluded_job_skills, *args, **kwargs
    ):
        """
        Initialize multi choice fields.
        """
        super().__init__(*args, **kwargs)

        self.fields['include_skills'] = forms.MultipleChoiceField(
            choices=((skill.id, skill.name) for skill in excluded_job_skills),
            required=False,
        )
        self.fields['exclude_skills'] = forms.MultipleChoiceField(
            choices=((skill.id, skill.name) for skill in job_skills),
            required=False,
        )
