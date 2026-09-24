"""
Serializers for taxonomy.
"""

from rest_framework import serializers

from taxonomy.models import Skill, SkillCategory, SkillSubCategory


class SkillCategorySerializer(serializers.ModelSerializer):
    """
    Skill Category model serializer.
    """

    class Meta:
        """
        Meta definition for SkillCategorySerializer.
        """

        model = SkillCategory
        fields = ('name',)


class SkillSubCategorySerializer(serializers.ModelSerializer):
    """
    Skill SubCategory model serializer.
    """

    category = SkillCategorySerializer()

    class Meta:
        """
        Meta definition for SkillSubCategorySerializer.
        """

        model = SkillSubCategory
        fields = ('name', 'category')


class SkillSerializer(serializers.ModelSerializer):
    """
    Serializer for the Skill model.
    """

    category = SkillCategorySerializer()
    subcategory = SkillSubCategorySerializer()

    class Meta:
        """
        Metadata for SkillSerializer.
        """

        model = Skill
        fields = ('name', 'description', 'category', 'subcategory')
