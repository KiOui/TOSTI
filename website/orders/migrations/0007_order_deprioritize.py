# Generated by Django 4.1.4 on 2022-12-28 13:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0006_alter_shift_max_orders_total"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="deprioritize",
            field=models.BooleanField(default=False),
        ),
    ]
