# Generated by Django 3.0.5 on 2020-07-06 15:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0005_auto_20200706_1651"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="ordervenue",
            options={
                "ordering": ["venue__name"],
                "permissions": [
                    ("can_order_in_venue", "Can order products during this shift"),
                    ("can_manage_shift_in_venue", "Can manage shifts"),
                ],
            },
        ),
    ]