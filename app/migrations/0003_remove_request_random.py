# Generated by Django 3.0.3 on 2020-02-18 00:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_request_random'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='request',
            name='random',
        ),
    ]
