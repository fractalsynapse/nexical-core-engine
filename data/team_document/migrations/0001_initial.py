# Generated by Django 4.1.13 on 2024-05-21 15:40

from django.db import migrations, models
import django.db.models.deletion
import systems.models.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('team_document_collection', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TeamDocument',
            fields=[
                ('created', models.DateTimeField(editable=False, null=True)),
                ('updated', models.DateTimeField(editable=False, null=True)),
                ('id', models.CharField(editable=False, max_length=64, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=256)),
                ('hash', models.CharField(default=None, max_length=65, null=True)),
                ('external_id', models.CharField(default=None, max_length=256, null=True)),
                ('text', models.TextField(default=None, null=True)),
                ('sentences', systems.models.fields.ListField(default=list)),
                ('team_document_collection', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(data_name)s', to='team_document_collection.teamdocumentcollection')),
            ],
            options={
                'verbose_name': 'team document',
                'verbose_name_plural': 'team documents',
                'db_table': 'engine_team_document',
                'ordering': ['id'],
                'abstract': False,
                'unique_together': {('team_document_collection', 'external_id')},
            },
        ),
    ]