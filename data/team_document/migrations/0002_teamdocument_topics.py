# Generated by Django 4.1.13 on 2024-05-21 23:31

from django.db import migrations
import systems.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('team_document', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='teamdocument',
            name='topics',
            field=systems.models.fields.DictionaryField(default=dict),
        ),
    ]