# Generated by Django 4.1.4 on 2023-01-26 09:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("thaliedje", "0011_alter_spotifyplayer_options"),
    ]

    operations = [
        migrations.AddField(
            model_name="marietjeplayer",
            name="client_id",
            field=models.CharField(default="", max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="marietjeplayer",
            name="client_secret",
            field=models.CharField(default="", max_length=255),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="marietjeplayer",
            name="url",
            field=models.URLField(default="", max_length=255),
        ),
    ]