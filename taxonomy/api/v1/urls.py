"""
Taxonomy v1 API URLs.
"""
from rest_framework.routers import DefaultRouter

from django.urls import path

from taxonomy.api.v1.views import (
    JobPostingsViewSet,
    JobsViewSet,
    JobTopSkillCategoriesAPIView,
    SkillsQuizViewSet,
    SkillViewSet,
)

ROUTER = DefaultRouter()

urlpatterns = [
    path(r'job-top-subcategories/<int:job_id>/', JobTopSkillCategoriesAPIView.as_view(), name='job_top_subcategories')
]

ROUTER.register(r'skills', SkillViewSet, basename='skill')
ROUTER.register(r'jobs', JobsViewSet, basename='job')
ROUTER.register(r'jobpostings', JobPostingsViewSet, basename='jobposting')
ROUTER.register(r'skills-quiz', SkillsQuizViewSet, basename='skills_quiz')

urlpatterns += ROUTER.urls
