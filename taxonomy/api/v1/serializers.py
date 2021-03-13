from rest_framework import serializers
from taxonomy.models import Skill


class SkillSerializer(serializers.ModelSerializer):
    """ Skill Searlizer """

    class Meta:
        model = Skill
        fields = ('name', 'description')
