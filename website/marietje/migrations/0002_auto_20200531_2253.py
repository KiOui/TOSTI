# Generated by Django 3.0.5 on 2020-05-31 20:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("marietje", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SpotifySettings",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("display_name", models.CharField(max_length=256, null=True)),
                ("playback_device_id", models.CharField(max_length=256, null=True)),
                ("client_id", models.CharField(max_length=256, unique=True)),
                ("client_secret", models.CharField(max_length=256)),
                ("redirect_uri", models.CharField(max_length=512)),
            ],
        ),
        migrations.DeleteModel(name="SpotifyAuthCode",),
    ]