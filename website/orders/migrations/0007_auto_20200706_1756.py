# Generated by Django 3.0.5 on 2020-07-06 15:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0006_auto_20200706_1754"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="ordervenue",
            options={
                "ordering": ["venue__name"],
                "permissions": [
                    (
                        "can_order_in_venue",
                        "Can order products during shifts in this venue",
                    ),
                    ("can_manage_shift_in_venue", "Can manage shifts in this venue"),
                ],
            },
        ),
    ]