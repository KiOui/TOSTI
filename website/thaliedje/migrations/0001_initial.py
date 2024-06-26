# Generated by Django 4.2.9 on 2024-04-08 12:50

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Player",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("display_name", models.CharField(blank=True, default="", max_length=255)),
                ("slug", models.SlugField(max_length=100, unique=True)),
            ],
            options={
                "verbose_name": "Player",
                "verbose_name_plural": "Players",
                "permissions": [
                    ("can_control", "Can control music players"),
                    ("can_request_playlists_and_albums", "Can request playlists and albums"),
                ],
            },
        ),
        migrations.CreateModel(
            name="PlayerLogEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(max_length=255)),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                ("description", models.CharField(max_length=255)),
            ],
            options={
                "verbose_name": "player log entry",
                "verbose_name_plural": "player log entries",
            },
        ),
        migrations.CreateModel(
            name="SpotifyArtist",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("artist_name", models.CharField(max_length=255)),
                ("artist_id", models.CharField(max_length=255, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name="SpotifyQueueItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("added", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["-added"],
            },
        ),
        migrations.CreateModel(
            name="SpotifyTrack",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("track_id", models.CharField(max_length=255, unique=True)),
                ("track_name", models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name="ThaliedjeBlacklistedUser",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("explanation", models.TextField(blank=True, null=True)),
            ],
            options={
                "verbose_name": "blacklisted user",
            },
        ),
        migrations.CreateModel(
            name="ThaliedjeControlEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("association_can_request", models.BooleanField(default=False)),
                ("association_can_control", models.BooleanField(default=False)),
                ("association_can_request_playlist", models.BooleanField(default=False)),
                (
                    "join_code",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        null=True,
                        validators=[django.core.validators.MinLengthValidator(20)],
                    ),
                ),
                ("selected_users_can_request", models.BooleanField(default=False)),
                ("selected_users_can_control", models.BooleanField(default=False)),
                ("selected_users_can_request_playlist", models.BooleanField(default=False)),
                ("everyone_can_request", models.BooleanField(default=False)),
                ("everyone_can_control", models.BooleanField(default=False)),
                ("everyone_can_request_playlist", models.BooleanField(default=False)),
                ("respect_blacklist", models.BooleanField(default=True)),
                ("check_throttling", models.BooleanField(default=True)),
            ],
            options={
                "verbose_name": "control event",
                "verbose_name_plural": "control events",
            },
        ),
        migrations.CreateModel(
            name="MarietjePlayer",
            fields=[
                (
                    "player_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="thaliedje.player",
                    ),
                ),
                ("url", models.URLField(default="", max_length=255)),
                ("client_id", models.CharField(max_length=100)),
                ("client_secret", models.CharField(max_length=255)),
            ],
            bases=("thaliedje.player",),
        ),
        migrations.CreateModel(
            name="SpotifyPlayer",
            fields=[
                (
                    "player_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="thaliedje.player",
                    ),
                ),
                ("playback_device_id", models.CharField(blank=True, default="", max_length=255)),
                (
                    "playback_device_name",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="When configuring this Spotify account for the first time, make sure to have the Spotify account active on at least one playback device to complete configuration.",
                        max_length=255,
                    ),
                ),
                ("client_id", models.CharField(max_length=255, unique=True)),
                ("client_secret", models.CharField(max_length=255)),
                ("redirect_uri", models.CharField(max_length=255)),
            ],
            options={
                "verbose_name": "Spotify player",
                "verbose_name_plural": "Spotify players",
                "permissions": [
                    ("can_control", "Can control music players"),
                    ("can_request_playlists_and_albums", "Can request playlists and albums"),
                ],
            },
            bases=("thaliedje.player",),
        ),
    ]
