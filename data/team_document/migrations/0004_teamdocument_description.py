# Generated by Django 4.1.13 on 2024-06-17 19:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('team_document', '0003_teamdocument_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='teamdocument',
            name='description',
            field=models.TextField(default=None, null=True),
        ),
    ]
