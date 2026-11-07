import django.core.validators
import django.db.models.deletion
import functools
import reimbursements.models
import utils.media.services
from django.db import migrations, models


def copy_receipts_to_reimbursement_receipts(apps, schema_editor):
    Reimbursement = apps.get_model("reimbursements", "Reimbursement")
    ReimbursementReceipt = apps.get_model(
        "reimbursements", "ReimbursementReceipt"
    )

    for reimbursement in Reimbursement.objects.exclude(receipt="").iterator():
        ReimbursementReceipt.objects.create(
            reimbursement_id=reimbursement.pk,
            file=reimbursement.receipt.name,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("reimbursements", "0006_merge_20250625_2032"),
    ]

    operations = [
        migrations.CreateModel(
            name="ReimbursementReceipt",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "file",
                    models.FileField(
                        upload_to=functools.partial(
                            utils.media.services._generic_upload_to,
                            prefix="reimbursements/receipts",
                            token_bytes=8,
                        ),
                        validators=[
                            django.core.validators.FileExtensionValidator(
                                allowed_extensions=["pdf", "jpg", "jpeg", "png"],
                                message="Only pdf, jpg, jpeg and png files are allowed.",
                            ),
                            reimbursements.models.validate_file_size,
                        ],
                    ),
                ),
                (
                    "reimbursement",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="receipts",
                        to="reimbursements.reimbursement",
                    ),
                ),
            ],
        ),
        migrations.RunPython(copy_receipts_to_reimbursement_receipts),
        migrations.RemoveField(
            model_name="reimbursement",
            name="receipt",
        ),
    ]
