# Generated by Django 4.1.13 on 2024-05-21 19:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('team', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='name',
            field=models.CharField(default='', max_length=256),
            preserve_default=False,
        ),
    ]
