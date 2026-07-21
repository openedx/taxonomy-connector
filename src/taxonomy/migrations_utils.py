"""
Utils used in migrations.
"""


def delete_all_records(apps, schema_editor):  # pylint: disable=unused-argument
    """
    Delete all records related to taxonomy.
    """
    table_names = ('CourseSkills', 'JobPostings', 'JobSkills', 'Job', 'Skill')
    for table_name in table_names:
        model = apps.get_model('taxonomy', table_name)
        model.objects.all().delete()
