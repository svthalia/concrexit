"""The models defined by the payments package"""
import uuid

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from localflavor.generic.countries.sepa import IBAN_SEPA_COUNTRIES
from localflavor.generic.models import IBANField, BICField


class Payment(models.Model):
    """
    Describes a payment
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created_at = models.DateTimeField(_("created at"), default=timezone.now)

    NONE = "no_payment"
    CASH = "cash_payment"
    CARD = "card_payment"
    TPAY = "tpay_payment"
    WIRE = "wire_payment"

    PAYMENT_TYPE = (
        (NONE, _("No payment")),
        (CASH, _("Cash payment")),
        (CARD, _("Card payment")),
        (TPAY, _("Thalia Pay payment")),
        (WIRE, _("Wire payment")),
    )

    type = models.CharField(
        choices=PAYMENT_TYPE, verbose_name=_("type"), max_length=20, default=NONE
    )

    amount = models.DecimalField(
        blank=False, null=False, max_digits=5, decimal_places=2
    )

    processing_date = models.DateTimeField(_("processing date"), blank=True, null=True,)

    paid_by = models.ForeignKey(
        "members.Member",
        models.CASCADE,
        related_name="paid_payment_set",
        blank=False,
        null=True,
    )

    processed_by = models.ForeignKey(
        "members.Member",
        models.CASCADE,
        related_name="processed_payment_set",
        blank=False,
        null=True,
    )

    notes = models.TextField(blank=True, null=True)

    @property
    def processed(self):
        return self.type != self.NONE

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        if self.type != self.NONE and not self.processing_date:
            self.processing_date = timezone.now()
        elif self.type == self.NONE:
            self.processing_date = None
        super().save(force_insert, force_update, using, update_fields)

    def get_admin_url(self):
        content_type = ContentType.objects.get_for_model(self.__class__)
        return reverse(
            "admin:%s_%s_change" % (content_type.app_label, content_type.model),
            args=(self.id,),
        )

    class Meta:
        verbose_name = _("payment")
        verbose_name_plural = _("payments")
        permissions = (("process_payments", _("Process payments")),)

    def __str__(self):
        return _("Payment of {amount}").format(amount=self.amount)


class BankAccount(models.Model):
    """
    Describes a bank account
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created_at = models.DateTimeField(_("created at"), default=timezone.now)

    last_used = models.DateField(verbose_name=_("last used"), blank=True, null=True,)

    owner = models.ForeignKey(
        to="members.Member",
        verbose_name=_("owner"),
        related_name="bank_accounts",
        on_delete=models.SET_NULL,
        blank=False,
        null=True,
    )

    initials = models.CharField(verbose_name=_("initials"), max_length=20,)

    last_name = models.CharField(verbose_name=_("last name"), max_length=255,)

    iban = IBANField(verbose_name=_("IBAN"), include_countries=IBAN_SEPA_COUNTRIES,)

    bic = BICField(
        verbose_name=_("BIC"),
        blank=True,
        null=True,
        help_text=_("This field is optional for Dutch bank accounts."),
    )

    valid_from = models.DateField(verbose_name=_("valid from"), blank=True, null=True,)

    valid_until = models.DateField(
        verbose_name=_("valid until"), blank=True, null=True,
    )

    signature = models.TextField(verbose_name=_("signature"), blank=True, null=True,)

    mandate_no = models.CharField(
        verbose_name=_("mandate number"),
        max_length=255,
        blank=True,
        null=True,
        unique=True,
    )

    def clean(self):
        super().clean()
        errors = {}

        if self.bic is None and self.iban[0:2] != "NL":
            errors.update(
                {"bic": _("This field is required for foreign bank accounts.")}
            )

        if not self.owner:
            errors.update({"owner": _("This field is required.")})

        mandate_fields = [
            ("valid_from", self.valid_from),
            ("signature", self.signature),
            ("mandate_no", self.mandate_no),
        ]

        if any(not field[1] for field in mandate_fields) and any(
            field[1] for field in mandate_fields
        ):
            for field in mandate_fields:
                if not field[1]:
                    errors.update(
                        {
                            field[0]: _(
                                "This field is required " "to complete the mandate."
                            )
                        }
                    )

        if self.valid_from and self.valid_until and self.valid_from > self.valid_until:
            errors.update(
                {"valid_until": _("This date cannot be before the from date.")}
            )

        if self.valid_until and not self.valid_from:
            errors.update({"valid_until": _("This field cannot have a value.")})

        if errors:
            raise ValidationError(errors)

    @property
    def name(self):
        return f"{self.initials} {self.last_name}"

    @property
    def valid(self):
        if self.valid_from is not None and self.valid_until is not None:
            return self.valid_from <= timezone.now().date() < self.valid_until
        return self.valid_from is not None and self.valid_from <= timezone.now().date()

    def __str__(self):
        return f"{self.iban} - {self.name}"

    class Meta:
        ordering = ("created_at",)
