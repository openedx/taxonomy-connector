"""
Taxonomy API views.
"""
from collections import OrderedDict
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from django.db.models import Count, Prefetch, Sum
from django.shortcuts import get_object_or_404

from taxonomy.api.filters import SkillNameFilter, XBlocksFilter
from taxonomy.api.permissions import IsOwner
from taxonomy.api.v1.serializers import (
    JobPostingsSerializer,
    JobSkillCategorySerializer,
    JobsListSerializer,
    SkillListSerializer,
    SkillsQuizSerializer,
    XBlocksSkillsSerializer,
)
from taxonomy.models import (
    CourseSkills,
    Job,
    JobPostings,
    Skill,
    SkillCategory,
    SkillsQuiz,
    SkillSubCategory,
    XBlockSkillData,
    XBlockSkills,
)


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
            ),
            Prefetch(
                'xblockskilldata_set',
                queryset=XBlockSkillData.objects.filter(is_blacklisted=False).select_related('xblock')
            ),
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


class JobTopSkillCategoriesAPIView(APIView):
    """
    This API takes job id as input and return job related top 5 skills categories.
    The top 5 skills categories also contains their skills and skills subcategories matching the job's skills.
    """
    permission_classes = [permissions.IsAdminUser]
    throttle_scope = 'taxonomy-api-throttle-scope'

    def get(self, request, job_id):
        """
        Example URL: GET https://discovery.edx.org/taxonomy/api/v1/job-top-subcategories/2/

        example response:
         {
            "job": "Digital Product Manager",
            "skill_categories": [
                {
                    "name": "Information Technology",
                    "id": 1,
                    "skills": [
                        {"id": 1, "name": "Technology Roadmap"},
                        {"id": 2, "name": "Query Languages"},
                        {"id": 3, "name": "MongoDB"},
                        // here only job related skills
                    ],
                    "skills_subcategories": [
                        {
                            "id": 1,
                            "name": "Databases",
                            skills: [
                                {"id": 1, "name": "Technology Roadmap"},
                                {"id": 2, "name": "Query Languages"},
                                {"id": 3, "name": "MongoDB"},
                                {"id": 5, "name": "DEF"},
                                // all skills in this subcategory
                            ]
                        },
                        {
                            "id": 2,
                            "name": "IT Management",
                            "skills": [
                                {"id": 1, "name": "Technology Roadmap"},
                                // all skills in this subcategory
                            ]
                        },
                        // job related skills subcategories
                    ]
                },
                // Here more 4 skill categories
            ]
        }

        """
        job = get_object_or_404(Job, id=job_id)
        skill_categories = SkillCategory.objects.filter(
            skills__jobskills__job=job
        ).prefetch_related(
            Prefetch(
                'skill_set',
                queryset=Skill.objects.filter(jobskills__job=job).distinct()
            ),
            Prefetch(
                'skillsubcategory_set',
                queryset=SkillSubCategory.objects.filter(skills__jobskills__job=job).distinct().prefetch_related('skill_set')
            ),
        ).annotate(
            total_significance=Sum('skills__jobskills__significance'),
            total_unique_postings=Sum('skills__jobskills__unique_postings'),
            total_skills=Count('skills'),
        ).order_by(
            '-total_significance', '-total_unique_postings', '-total_skills'
        )[:5]

        response_data = JobSkillCategorySerializer(job, context={'skill_categories': skill_categories}).data
        return Response(response_data)


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


class JobHolderUsernamesAPIView(APIView):
    """
    THis API takes a job id as input and returns a list of 100 usernames
    of job holders after querying the most recent SkillsQuiz table entries.
    This API is available only to the admin users.
    """
    permission_classes = [permissions.IsAdminUser]
    throttle_scope = 'taxonomy-api-throttle-scope'

    def get(self, request, job_id):
        """
        Example URL: GET https://discovery.edx.org/taxonomy/api/v1/job-holder-usernames/2/

        Example Response:
        {
            "usernames": [
                "user1",
                "user2",
                "user3",
                "user4",
                "user5",
                // 95 more usernames
            ]
        }
        """
        job = get_object_or_404(Job, id=job_id)

        usernames_queryset = SkillsQuiz.objects.filter(
            current_job=job,
        ).order_by('-id').values_list('username', flat=True)[:5000]
        usernames = list(OrderedDict.fromkeys(usernames_queryset))[:100]

        return Response({"usernames": usernames})


class XBlockSkillsViewSet(TaxonomyAPIViewSetMixin, RetrieveModelMixin, ListModelMixin, GenericViewSet):
    """
    ViewSet to list and retrieve all XBlockSkills in the system.
    """
    serializer_class = XBlocksSkillsSerializer
    permission_classes = (permissions.IsAuthenticated, )
    filter_backends = (DjangoFilterBackend,)
    filterset_class = XBlocksFilter

    def get_queryset(self):
        """
        Get all the xblocks skills with prefetch_related objects.
        """
        return XBlockSkills.objects.all().prefetch_related(
            Prefetch(
                'skills',
                queryset=Skill.objects.filter(xblockskilldata__is_blacklisted=False),
            ),
        )
