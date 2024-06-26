# Generated by Django 5.0.4 on 2024-04-28 19:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0002_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="picked_up",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="order",
            name="picked_up_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
