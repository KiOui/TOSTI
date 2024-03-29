# Generated by Django 3.2.13 on 2022-07-05 11:54

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('thaliedje', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='current_volume',
            field=models.PositiveSmallIntegerField(blank=True, null=True, validators=[django.core.validators.MaxValueValidator(100)]),
        ),
        migrations.AlterField(
            model_name='player',
            name='playback_device_name',
            field=models.CharField(blank=True, default='', help_text='When configuring this Spotify account for the first time, make sure to have the Spotify account active on at least one playback device to complete configuration.', max_length=255),
        ),
    ]
