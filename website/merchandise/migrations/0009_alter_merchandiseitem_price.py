# Generated by Django 4.1.3 on 2023-01-25 20:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("merchandise", "0008_alter_merchandiseitem_image"),
    ]

    operations = [
        migrations.AlterField(
            model_name="merchandiseitem",
            name="price",
            field=models.DecimalField(decimal_places=2, max_digits=8),
        ),
    ]
