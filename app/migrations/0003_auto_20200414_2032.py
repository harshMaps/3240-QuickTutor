# Generated by Django 3.0.2 on 2020-04-15 00:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_user_reviewable_user'),
    ]

    operations = [
        migrations.RenameField(
            model_name='user',
            old_name='reviewable_user',
            new_name='reviewable_tutee',
        ),
        migrations.AddField(
            model_name='user',
            name='reviewable_tutor',
            field=models.CharField(default='None', max_length=100),
        ),
    ]
