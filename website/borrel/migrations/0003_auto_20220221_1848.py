# Generated by Django 3.2.10 on 2022-02-21 17:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('borrel', '0002_auto_20211019_2107'),
    ]

    operations = [
        migrations.RenameField(
            model_name='reservationitem',
            old_name='remarks',
            new_name='product_description',
        ),
        migrations.RemoveField(
            model_name='reservationitem',
            name='product_unit_description',
        ),
        migrations.AlterField(
            model_name='reservationitem',
            name='amount_reserved',
            field=models.PositiveIntegerField(default=1),
            preserve_default=False,
        ),
        migrations.RenameModel(
            old_name='BorrelInventoryCategory',
            new_name='ProductCategory',
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('active', models.BooleanField(default=True)),
                ('description', models.TextField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=6)),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='products', to='borrel.productcategory')),
            ],
        ),
        migrations.AlterField(
            model_name='reservationitem',
            name='product',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='borrel.product'),
        ),
        migrations.DeleteModel(
            name='BorrelInventoryProduct',
        ),
    ]