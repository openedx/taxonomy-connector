"""
Taxonomy API views.
"""
from rest_framework import permissions
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet

from django.db.models import Prefetch

from taxonomy.api.v1.serializers import JobPostingsSerializer, JobsListSerializer, SkillListSerializer
from taxonomy.models import CourseSkills, Job, JobPostings, Skill


class TaxonomyAPIViewSetMixin:
    """
    Taxonomy APIs ViewSet Mixin.
    """
    permission_classes = (permissions.IsAuthenticated,)
    throttle_scope = 'taxonomy-api-throttle-scope'


class SkillViewSet(TaxonomyAPIViewSetMixin, RetrieveModelMixin, ListModelMixin, GenericViewSet):
    """
    ViewSet to list and retrieve all Skills in the system.
    """

    serializer_class = SkillListSerializer

    def get_queryset(self):
        """
        Get all the skills with prefetch_related objects.
        """
        return Skill.objects.all().prefetch_related(
            Prefetch(
                'courseskills_set',
                queryset=CourseSkills.objects.filter(is_blacklisted=False)
            )
        )


class JobsViewSet(TaxonomyAPIViewSetMixin, RetrieveModelMixin, ListModelMixin, GenericViewSet):
    """
    ViewSet to list and retrieve all Jobs in the system.
    """
    serializer_class = JobsListSerializer

    def get_queryset(self):
        """
        Get all the jobs with prefetch_related objects.
        """
        return Job.objects.all().prefetch_related(
            'jobskills_set', 'jobskills_set__skill'
        )


class JobPostingsViewSet(TaxonomyAPIViewSetMixin, RetrieveModelMixin, ListModelMixin, GenericViewSet):
    """
    ViewSet to list and retrieve all JobPostings in the system.
    """
    serializer_class = JobPostingsSerializer

    def get_queryset(self):
        """
        Get all the jobpostings with prefetch_related objects.
        """
        return JobPostings.objects.all().select_related(
            'job'
        )
