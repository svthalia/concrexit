import django.db.models.deletion
from django.db import migrations, models


def copy_uploaded_receipts(apps, schema_editor):
    MoneybirdReceipt = apps.get_model(
        "moneybirdsynchronization", "MoneybirdReceipt"
    )
    MoneybirdReceiptAttachment = apps.get_model(
        "moneybirdsynchronization", "MoneybirdReceiptAttachment"
    )

    for moneybird_receipt in MoneybirdReceipt.objects.select_related(
        "reimbursement"
    ).iterator():
        reimbursement_receipt = moneybird_receipt.reimbursement.receipts.first()
        if reimbursement_receipt is not None:
            MoneybirdReceiptAttachment.objects.create(
                moneybird_receipt_id=moneybird_receipt.pk,
                reimbursement_receipt_id=reimbursement_receipt.pk,
                is_uploaded=moneybird_receipt.moneybird_attachment_is_uploaded,
            )


class Migration(migrations.Migration):
    dependencies = [
        ("moneybirdsynchronization", "0012_remove_moneybirdreceipt_moneybird_attachment_id_and_more"),
        ("reimbursements", "0007_reimbursementreceipt"),
    ]

    operations = [
        migrations.CreateModel(
            name="MoneybirdReceiptAttachment",
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
                ("is_uploaded", models.BooleanField(default=False)),
                (
                    "moneybird_receipt",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attachments",
                        to="moneybirdsynchronization.moneybirdreceipt",
                    ),
                ),
                (
                    "reimbursement_receipt",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="moneybird_attachment",
                        to="reimbursements.reimbursementreceipt",
                    ),
                ),
            ],
        ),
        migrations.RunPython(copy_uploaded_receipts),
    ]
