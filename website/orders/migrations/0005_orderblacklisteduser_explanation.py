# Generated by Django 3.2.14 on 2022-07-19 08:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0004_auto_20220712_1119'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderblacklisteduser',
            name='explanation',
            field=models.TextField(blank=True, null=True),
        ),
    ]
