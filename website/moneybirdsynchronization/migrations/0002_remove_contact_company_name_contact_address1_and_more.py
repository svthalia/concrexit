# Generated by Django 4.1.7 on 2023-02-22 13:47

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("moneybirdsynchronization", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="contact",
            name="company_name",
        ),
        migrations.AddField(
            model_name="contact",
            name="address1",
            field=models.CharField(
                blank=True, max_length=255, null=True, verbose_name="address 1"
            ),
        ),
        migrations.AddField(
            model_name="contact",
            name="address2",
            field=models.CharField(
                blank=True, max_length=255, null=True, verbose_name="address 2"
            ),
        ),
        migrations.AddField(
            model_name="contact",
            name="city",
            field=models.CharField(
                blank=True, max_length=255, null=True, verbose_name="city"
            ),
        ),
        migrations.AddField(
            model_name="contact",
            name="country",
            field=models.CharField(
                blank=True, max_length=255, null=True, verbose_name="country"
            ),
        ),
        migrations.AddField(
            model_name="contact",
            name="email",
            field=models.EmailField(
                blank=True, max_length=254, null=True, verbose_name="email"
            ),
        ),
        migrations.AddField(
            model_name="contact",
            name="zipcode",
            field=models.CharField(
                blank=True, max_length=255, null=True, verbose_name="zipcode"
            ),
        ),
    ]