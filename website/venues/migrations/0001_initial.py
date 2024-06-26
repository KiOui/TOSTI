# Generated by Django 4.2.9 on 2024-04-08 12:50

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("associations", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Venue",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=50, unique=True)),
                ("slug", models.SlugField(max_length=100, unique=True)),
                ("active", models.BooleanField(default=True)),
                (
                    "color_in_calendar",
                    models.CharField(
                        blank=True, help_text="Color of reservations shown in calendar.", max_length=50, null=True
                    ),
                ),
                ("can_be_reserved", models.BooleanField(default=True)),
                (
                    "automatically_accept_first_reservation",
                    models.BooleanField(
                        default=False,
                        help_text="If enabled, a reservation placed on this venue will be automatically accepted if it does not overlap with another reservation.",
                    ),
                ),
            ],
            options={
                "ordering": ["-active", "name"],
            },
        ),
        migrations.CreateModel(
            name="Reservation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=100)),
                ("start", models.DateTimeField()),
                ("end", models.DateTimeField()),
                (
                    "needs_music_keys",
                    models.BooleanField(
                        default=False, help_text="Whether the music keys are needed during this reservation."
                    ),
                ),
                ("comments", models.TextField(blank=True, null=True)),
                ("accepted", models.BooleanField(blank=True, default=None, null=True)),
                (
                    "join_code",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        null=True,
                        unique=True,
                        validators=[django.core.validators.MinLengthValidator(20)],
                    ),
                ),
                (
                    "association",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="reservations",
                        to="associations.association",
                    ),
                ),
                (
                    "user_created",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="reservations_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "user_updated",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="reservations_updated",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "users_access",
                    models.ManyToManyField(
                        blank=True, related_name="reservations_access", to=settings.AUTH_USER_MODEL
                    ),
                ),
                (
                    "venue",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="reservations", to="venues.venue"
                    ),
                ),
            ],
            options={
                "ordering": ["-start", "-end", "title"],
            },
        ),
    ]
