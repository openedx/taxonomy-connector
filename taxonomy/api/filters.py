"""
Filters for the Taxonomy connector APIs.
"""

from django_filters import rest_framework as filters

from django.db.models import Prefetch

from taxonomy.models import Skill, XBlockSkills


class SkillNameFilter(filters.FilterSet):
    """
    Filter skills by name. Supports filtering by comma-delimited string of names.
    """
    name = filters.CharFilter(method='filter_by_name')

    class Meta:
        model = Skill
        fields = ['name']

    def filter_by_name(self, queryset, _, value):  # pylint: disable=unused-argument
        """
        Filter skills by name.
        """
        skill_names = value.strip().split(',')
        return queryset.filter(name__in=skill_names)


class XBlocksFilter(filters.FilterSet):
    """
    Filter XBlocks by usage_key and verified flag. Supports filtering by
    comma-delimited string of usage_keys.
    """
    usage_key = filters.CharFilter(method='filter_by_usage_key', label='Usage key')
    verified = filters.BooleanFilter(method='filter_skills_by_verified', label='Verified')

    class Meta:
        model = XBlockSkills
        fields = ['usage_key', 'verified']

    def filter_by_usage_key(self, queryset, _, value):
        """
        Filter xblocks by usage_key.
        """
        usage_keys = value.strip().split(',')
        return queryset.filter(usage_key__in=usage_keys)

    def filter_skills_by_verified(self, queryset, _, value):
        """
        Filter skills by verified flag.
        """
        return queryset.prefetch_related(None).prefetch_related(
            Prefetch(
                'skills',
                queryset=Skill.objects.filter(
                    xblockskilldata__is_blacklisted=False,
                    xblockskilldata__verified=value,
                ).only(
                    'id',
                    'name'
                ).distinct(),
            ))
