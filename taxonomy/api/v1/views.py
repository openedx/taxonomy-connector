from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from taxonomy.models import Skill
from taxonomy.api.v1.serializers import SkillSerializer


class SkillsView(ListAPIView):
    """ List view for Skills """
    permission_classes = [IsAuthenticated]
    serializer_class = SkillSerializer

    def get_queryset(self):
        search = self.request.query_params.get('search')

        queryset = Skill.objects.exclude(courseskills__is_blacklisted=True)
        if search:
            queryset = queryset.filter(name__icontains=search)

        return queryset
