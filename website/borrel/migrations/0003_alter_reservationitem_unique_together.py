# Generated by Django 3.2.14 on 2022-07-07 13:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('borrel', '0002_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='reservationitem',
            unique_together={('reservation', 'product_name')},
        ),
    ]
