# Generated by Django 4.1.7 on 2023-03-15 18:46

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("pizzas", "0017_alter_product_price"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="foodevent",
            name="end_reminder",
        ),
    ]
