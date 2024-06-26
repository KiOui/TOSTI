# Generated by Django 4.2.9 on 2024-04-08 12:50

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("associations", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="BasicBorrelBrevet",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("registered_on", models.DateField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="BorrelReservation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("submitted_at", models.DateTimeField(blank=True, null=True)),
                ("title", models.CharField(max_length=100)),
                ("start", models.DateTimeField()),
                ("end", models.DateTimeField(blank=True, null=True)),
                ("comments", models.TextField(blank=True, null=True)),
                ("accepted", models.BooleanField(blank=True, default=None, null=True)),
                (
                    "join_code",
                    models.CharField(
                        blank=True, max_length=255, validators=[django.core.validators.MinLengthValidator(20)]
                    ),
                ),
                (
                    "association",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="borrel_reservations",
                        to="associations.association",
                    ),
                ),
            ],
            options={
                "ordering": ["-start", "-end", "title"],
            },
        ),
        migrations.CreateModel(
            name="Product",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True)),
                ("active", models.BooleanField(default=True)),
                ("description", models.TextField(blank=True, null=True)),
                ("price", models.DecimalField(decimal_places=2, max_digits=6)),
                ("can_be_reserved", models.BooleanField(default=True)),
                ("can_be_submitted", models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name="ProductCategory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100)),
            ],
            options={
                "verbose_name": "product category",
                "verbose_name_plural": "product categories",
            },
        ),
        migrations.CreateModel(
            name="ReservationItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("product_name", models.CharField(max_length=100)),
                ("product_description", models.TextField(blank=True, null=True)),
                ("product_price_per_unit", models.DecimalField(decimal_places=2, max_digits=6)),
                ("amount_reserved", models.PositiveIntegerField()),
                ("amount_used", models.PositiveIntegerField(blank=True, null=True)),
                (
                    "product",
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="borrel.product"
                    ),
                ),
                (
                    "reservation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="borrel.borrelreservation",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="product",
            name="category",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="products",
                to="borrel.productcategory",
            ),
        ),
    ]
