# Generated by Django 3.0.2 on 2020-04-15 01:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='user',
            old_name='reviewable_tutee',
            new_name='reviewable_user',
        ),
        migrations.RemoveField(
            model_name='user',
            name='reviewable_tutor',
        ),
    ]
