"""
Serializers for taxonomy.
"""

from rest_framework import serializers

from taxonomy.models import Skill


class SkillSerializer(serializers.ModelSerializer):
    """
    Serializer for the Skill model.
    """

    class Meta:
        """
        Metadata for SkillSerializer.
        """

        model = Skill
        fields = ('name', 'description')
