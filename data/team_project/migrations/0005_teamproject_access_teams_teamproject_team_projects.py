# Generated by Django 4.1.13 on 2024-07-07 22:35

from django.db import migrations, models
import systems.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('team_project', '0004_alter_teamproject_summary_format_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='teamproject',
            name='access_teams',
            field=systems.models.fields.ListField(default=list),
        ),
    ]