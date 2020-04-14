# Generated by Django 3.0.2 on 2020-04-14 19:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0005_auto_20200407_2130'),
    ]

    operations = [
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(max_length=500)),
                ('rating', models.IntegerField()),
                ('reviewee', models.CharField(max_length=100)),
                ('reviewer', models.CharField(max_length=100)),
            ],
        ),
    ]
