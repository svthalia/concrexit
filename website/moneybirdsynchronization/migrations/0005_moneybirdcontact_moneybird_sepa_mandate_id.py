# Generated by Django 4.2.5 on 2023-10-04 18:14

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("moneybirdsynchronization", "0004_moneybirdproject"),
    ]

    operations = [
        migrations.AddField(
            model_name="moneybirdcontact",
            name="moneybird_sepa_mandate_id",
            field=models.CharField(
                blank=True,
                max_length=255,
                null=True,
                unique=True,
                verbose_name="Moneybird SEPA mandate ID",
            ),
        ),
    ]
