# Generated by Django 3.0.2 on 2020-04-15 02:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_auto_20200414_2111'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='rating_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='user',
            name='rating_score',
            field=models.IntegerField(default=0),
        ),
    ]