from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from django.db import models

from members.models import Member
from payments.models import PaymentAmountField


class Reimbursement(models.Model):
    class Verdict(models.TextChoices):
        APPROVED = "approved", "Approved"
        DENIED = "denied", "Denied"

    owner = models.ForeignKey(
        model=Member,
        related_name="reimbursements",
        on_delete=models.PROTECT,
    )

    amount = PaymentAmountField(
        max_digits=5,
        decimal_places=2,
        help_text="How much did you pay (in euros)?",
    )

    date_incurred = models.DateField(
        help_text="When was this payment made?",
    )

    description = models.TextField(
        max_length=512,
        help_text="Why did you make this payment?",
        validators=[MinLengthValidator(10)],
    )

    # explicitely chose for FileField over an ImageField because companies often send invoices as pdf
    # TODO: verify file location
    receipt = models.FileField(upload_to="receipts/")

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

    evaluated_at = models.DateTimeField(null=True)
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
        if self.date_incurred > self.created.date():
            errors["date_incurred"] = "The date incurred cannot be in the future."

        if self.verdict == self.Verdict.DENIED and not self.verdict_clarification:
            errors["verdict_clarification"] = (
                "You must provide a reason for the denial."
            )

        if (
            self.verdict == self.Verdict.APPROVED
            or self.verdict == self.Verdict.DENIED
            and not self.evaluated_by
        ):
            errors["evaluated_by"] = "You must provide the evaluator."

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"Reimbursement #{self.id}"
