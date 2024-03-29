# Generated by Django 3.2.16 on 2022-12-10 15:00

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('venues', '0003_auto_20221210_1600'),
        ('thaliedje', '0008_auto_20221007_1626'),
    ]

    operations = [
        migrations.CreateModel(
            name='ThaliedjeControlEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('association_can_request', models.BooleanField(default=False)),
                ('association_can_control', models.BooleanField(default=False)),
                ('association_can_request_playlist', models.BooleanField(default=False)),
                ('join_code', models.CharField(blank=True, max_length=255, null=True, validators=[django.core.validators.MinLengthValidator(20)])),
                ('selected_users_can_request', models.BooleanField(default=False)),
                ('selected_users_can_control', models.BooleanField(default=False)),
                ('selected_users_can_request_playlist', models.BooleanField(default=False)),
                ('everyone_can_request', models.BooleanField(default=False)),
                ('everyone_can_control', models.BooleanField(default=False)),
                ('everyone_can_request_playlist', models.BooleanField(default=False)),
                ('respect_blacklist', models.BooleanField(default=True)),
                ('event', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='venues.reservation')),
                ('selected_users', models.ManyToManyField(blank=True, related_name='thaliedje_control_events', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'control event',
                'verbose_name_plural': 'control events',
            },
        ),
        migrations.CreateModel(
            name='PlayerLogEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(max_length=255)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('description', models.CharField(max_length=255)),
                ('player', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='thaliedje.player')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'player log entry',
                'verbose_name_plural': 'player log entries',
            },
        ),
    ]
