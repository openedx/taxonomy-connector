# Generated migration for MariaDB UUID field conversion (Django 5.2)
"""
Migration to convert UUIDField from char(32) to uuid type for MariaDB compatibility.
"""

from django.db import migrations


def apply_mariadb_migration(apps, schema_editor):
    connection = schema_editor.connection
    if connection.vendor != 'mysql':
        return
    with connection.cursor() as cursor:
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        if 'mariadb' not in version.lower():
            return
    with connection.cursor() as cursor:
        cursor.execute("ALTER TABLE taxonomy_refreshxblockskilldataconfig MODIFY uuid uuid NOT NULL")


def reverse_mariadb_migration(apps, schema_editor):
    connection = schema_editor.connection
    if connection.vendor != 'mysql':
        return
    with connection.cursor() as cursor:
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        if 'mariadb' not in version.lower():
            return
    with connection.cursor() as cursor:
        cursor.execute("ALTER TABLE taxonomy_refreshxblockskilldataconfig MODIFY uuid char(32) NOT NULL")


class Migration(migrations.Migration):
    dependencies = [
        ('taxonomy', '0037_alter_xblockskilldata_is_blacklisted_and_more'),
    ]
    operations = [
        migrations.RunPython(
            code=apply_mariadb_migration,
            reverse_code=reverse_mariadb_migration,
        ),
    ]
