# Generated by Django 4.1.13 on 2024-06-06 07:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('team_project', '0003_teamproject_repetition_penalty_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='teamproject',
            name='summary_format',
            field=models.TextField(default=None, null=True),
        ),
        migrations.AlterField(
            model_name='teamproject',
            name='summary_persona',
            field=models.TextField(default=None, null=True),
        ),
    ]
