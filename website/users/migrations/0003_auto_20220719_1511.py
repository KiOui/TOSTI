# Generated by Django 3.2.14 on 2022-07-19 13:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_rename_name_user_display_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='override_display_name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='override_short_name',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]