# Generated by Django 4.2.6 on 2023-10-26 13:34

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("moneybirdsynchronization", "0008_merge_20231024_1111"),
    ]

    operations = [
        migrations.AddField(
            model_name="moneybirdsalesinvoice",
            name="needs_deletion",
            field=models.BooleanField(
                default=False,
                help_text="Indicates that the invoice has to be deleted from moneybird.",
            ),
        ),
        migrations.AddField(
            model_name="moneybirdsalesinvoice",
            name="needs_synchronization",
            field=models.BooleanField(
                default=True,
                help_text="Indicates that the invoice has to be synchronized (again).",
            ),
        ),
    ]
