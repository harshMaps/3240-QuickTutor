# Generated by Django 3.0.3 on 2020-02-26 17:22

import app.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0019_auto_20200226_1219'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='user',
            managers=[
                ('objects', app.models.UserManager()),
            ],
        ),
    ]
