# Generated by Django 4.1.13 on 2024-05-22 05:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('team_document_collection', '0001_initial'),
        ('team_project', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='teamproject',
            name='team_document_collections',
            field=models.ManyToManyField(blank=True, related_name='%(data_name)s', to='team_document_collection.teamdocumentcollection'),
        ),
    ]
