from django.core.exceptions import ValidationError
from django.core.validators import (
    FileExtensionValidator,
    MinLengthValidator,
    MinValueValidator,
)
from django.db import models
from django.utils import timezone

from payments.models import PaymentAmountField
from utils.media.services import get_upload_to_function


def validate_file_size(file):
    max_size_mb = 10
    if file.size > max_size_mb * 1000 * 1000:
        raise ValidationError(f"File size must be less than {max_size_mb} MB")


class Reimbursement(models.Model):
    class Verdict(models.TextChoices):
        APPROVED = "approved", "Approved"
        DENIED = "denied", "Denied"

    owner = models.ForeignKey(
        "members.Member",
        related_name="reimbursements",
        on_delete=models.PROTECT,
    )

    amount = PaymentAmountField(
        max_digits=5,
        decimal_places=2,
        help_text="How much did you pay (in euros)?",
        validators=[
            MinValueValidator(0),
        ],
    )

    date_incurred = models.DateField(
        help_text="When was this payment made?",
    )

    description = models.TextField(
        max_length=512,
        help_text="Why did you make this payment?",
        validators=[MinLengthValidator(10)],
    )

    # FileField and not ImageField because companies often send invoices as pdf
    receipt = models.FileField(
        upload_to=get_upload_to_function("reimbursements/receipts"),
        validators=[
            FileExtensionValidator(
                allowed_extensions=["pdf", "jpg", "jpeg", "png"],
                message="Only pdf, jpg, jpeg and png files are allowed.",
            ),
            validate_file_size,
        ],
    )

    created = models.DateTimeField(auto_now_add=True)

    verdict = models.CharField(
        max_length=40,
        choices=Verdict.choices,
        null=True,
        blank=True,
    )

    verdict_clarification = models.TextField(
        help_text="Why did you choose this verdict?",
        null=True,
        blank=True,
    )

    evaluated_at = models.DateTimeField(null=True, editable=False)

    evaluated_by = models.ForeignKey(
        "auth.User",
        related_name="reimbursements_approved",
        on_delete=models.SET_NULL,
        editable=False,
        null=True,
    )

    class Meta:
        ordering = ["created"]

    def clean(self):
        super().clean()

        errors = {}

        if (
            self.date_incurred is not None
            and self.date_incurred > timezone.now().date()
        ):
            errors["date_incurred"] = "The date incurred cannot be in the future."

        if self.verdict == self.Verdict.DENIED and not self.verdict_clarification:
            errors["verdict_clarification"] = (
                "You must provide a reason for the denial."
            )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"Reimbursement #{self.id}"
