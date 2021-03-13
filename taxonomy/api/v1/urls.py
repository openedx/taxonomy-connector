from django.urls import path
from taxonomy.api.v1.views import SkillsView

urlpatterns = [
    path('api/v1/skills/', SkillsView.as_view(), name='skill_list')
]
