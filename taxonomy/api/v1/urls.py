"""
Taxonomy v1 API URLs.
"""
from rest_framework.routers import DefaultRouter

from taxonomy.api.v1.views import JobPostingsViewSet, JobsViewSet, SkillViewSet

router = DefaultRouter()
router.register(r'skills', SkillViewSet, basename='skill')
router.register(r'jobs', JobsViewSet, basename='job')
router.register(r'jobpostings', JobPostingsViewSet, basename='jobposting')

urlpatterns = router.urls
