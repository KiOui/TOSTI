# Generated by Django 3.2.10 on 2022-03-01 15:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('venues', '0004_auto_20211211_1158'),
    ]

    operations = [
        migrations.RenameField(
            model_name='reservation',
            old_name='end_time',
            new_name='end',
        ),
        migrations.RenameField(
            model_name='reservation',
            old_name='start_time',
            new_name='start',
        ),
    ]