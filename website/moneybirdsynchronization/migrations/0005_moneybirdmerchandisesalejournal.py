# Generated by Django 4.2.6 on 2023-10-18 13:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("merchandise", "0011_merchandisesale_merchandiseitem_purchase_price_and_more"),
        ("moneybirdsynchronization", "0004_moneybirdproject"),
    ]

    operations = [
        migrations.CreateModel(
            name="MoneybirdMerchandiseSaleJournal",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "moneybird_general_journal_document_id",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        null=True,
                        verbose_name="moneybird general journal document id",
                    ),
                ),
                (
                    "external_invoice",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="moneybird_journal_external_invoice",
                        to="moneybirdsynchronization.moneybirdexternalinvoice",
                        verbose_name="external invoice",
                    ),
                ),
                (
                    "merchandise_sale",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="moneybird_journal_merchandise_sale",
                        to="merchandise.merchandisesale",
                        verbose_name="merchandise sale",
                    ),
                ),
            ],
            options={
                "verbose_name": "moneybird merchandise sale journal",
                "verbose_name_plural": "moneybird merchandise sale journals",
            },
        ),
    ]