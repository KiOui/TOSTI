# Generated by Django 3.2.15 on 2022-10-23 10:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('borrel', '0005_auto_20220719_1328'),
        ('tantalus', '0003_rename_tantalusproduct_tantalusordersproduct'),
    ]

    operations = [
        migrations.CreateModel(
            name='TantalusBorrelProduct',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tantalus_id', models.PositiveIntegerField()),
                ('product', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='borrel.product')),
            ],
        ),
    ]