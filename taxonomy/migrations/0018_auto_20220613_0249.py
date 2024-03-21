# Generated by Django 3.2.12 on 2022-06-13 02:49

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models

import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('taxonomy', '0017_auto_20220214_0214'),
    ]

    operations = [
        migrations.CreateModel(
            name='SkillCategory',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('id', models.IntegerField(help_text='Category id, this is the same id as received from EMSI API.', primary_key=True, serialize=False)),
                ('name', models.CharField(help_text='The name of the category.', max_length=255)),
            ],
            options={
                'verbose_name': 'Skill Category',
                'verbose_name_plural': 'Skill Categories',
                'ordering': ('id',),
            },
        ),
        migrations.CreateModel(
            name='SkillSubCategory',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('id', models.IntegerField(help_text='Sub category id, this is the same id as received from EMSI API.', primary_key=True, serialize=False)),
                ('name', models.CharField(help_text='The name of the subcategory.', max_length=255)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_query_name='sub_categories', to='taxonomy.skillcategory')),
            ],
            options={
                'verbose_name': 'Skill Subcategory',
                'verbose_name_plural': 'Skill Subcategories',
                'ordering': ('id',),
            },
        ),
        migrations.AddField(
            model_name='skill',
            name='category',
            field=models.ForeignKey(blank=True, help_text='Category this skill belongs to.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_query_name='skills', to='taxonomy.skillcategory'),
        ),
        migrations.AddField(
            model_name='skill',
            name='subcategory',
            field=models.ForeignKey(blank=True, help_text='Sub category this skill belongs to.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_query_name='skills', to='taxonomy.skillsubcategory'),
        ),
    ]
