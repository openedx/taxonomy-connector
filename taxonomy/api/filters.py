"""
Filters for the Taxonomy connector APIs.
"""

from django_filters import rest_framework as filters

from taxonomy.models import Skill


class SkillNameFilter(filters.FilterSet):
    """
    Filter skills by name. Supports filtering by comma-delimited string of names.
    """
    name = filters.CharFilter(method='filter_by_name')

    class Meta:
        model = Skill
        fields = ['name']

    def filter_by_name(self, queryset, name, value):  # pylint: disable=unused-argument
        skill_names = value.strip().split(',')
        return queryset.filter(name__in=skill_names)
