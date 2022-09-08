"""
Taxonomy API views.
"""
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from django.db.models import Prefetch

from taxonomy.api.filters import SkillNameFilter
from taxonomy.api.permissions import IsOwner
from taxonomy.api.v1.serializers import (
    JobPostingsSerializer,
    JobsListSerializer,
    SkillListSerializer,
    SkillsQuizSerializer,
)
from taxonomy.models import CourseSkills, Job, JobPostings, Skill, SkillsQuiz


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
    filter_backends = (DjangoFilterBackend,)
    filterset_class = SkillNameFilter

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


class SkillsQuizViewSet(TaxonomyAPIViewSetMixin, ModelViewSet):
    """
    ViewSet to list and retrieve all JobPostings in the system.
    """
    serializer_class = SkillsQuizSerializer
    permission_classes = (permissions.IsAuthenticated, IsOwner | permissions.IsAdminUser, )
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('username', )

    queryset = SkillsQuiz.objects.all()

    def perform_create(self, serializer):
        """
        Attach the User to the SkillsQuiz Model by overriding perform_create method.
        """
        serializer.save(username=self.request.user)

    def get_queryset(self):
        """
        User should only be able to access its own quiz.
        """
        queryset = self.queryset
        # Non staff user should only be able to access their own records.
        if not self.request.user.is_staff:
            queryset = queryset.filter(username=self.request.user.username)

        return queryset.all().select_related('current_job').prefetch_related('skills', 'future_jobs')
