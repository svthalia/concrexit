"""The models defined by the payments package."""
import datetime
import uuid
from decimal import Decimal

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import DEFERRED, Q, Sum, BooleanField, DecimalField
from django.db.models.expressions import Case, When, Value
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from localflavor.generic.countries.sepa import IBAN_SEPA_COUNTRIES
from localflavor.generic.models import IBANField, BICField
from queryable_properties.managers import QueryablePropertiesManager
from queryable_properties.properties import queryable_property, AggregateProperty

from members.models import Member


class PaymentUser(Member):
    class Meta:
        proxy = True
        verbose_name = "payment user"

    objects = QueryablePropertiesManager()

    @queryable_property(annotation_based=True)
    @classmethod
    def tpay_enabled(cls):
        today = timezone.now().date()
        return Case(
            When(
                Q(
                    bank_accounts__valid_from__isnull=False,
                    bank_accounts__valid_from__lte=today,
                )
                & (
                    Q(bank_accounts__valid_until__isnull=True)
                    | Q(bank_accounts__valid_until__gt=today)
                ),
                then=settings.THALIA_PAY_ENABLED_PAYMENT_METHOD,
            ),
            default=False,
            output_field=BooleanField(),
        )

    tpay_balance = AggregateProperty(
        -1
        * Coalesce(
            Sum(
                "paid_payment_set__amount",
                filter=Q(paid_payment_set__type="tpay_payment")
                & (
                    Q(paid_payment_set__batch__isnull=True)
                    | Q(paid_payment_set__batch__processed=False)
                ),
            ),
            Value(0.00),
            output_field=DecimalField(decimal_places=2, max_digits=6),
        )
    )

    @queryable_property(annotation_based=True)
    @classmethod
    def tpay_allowed(cls):
        return Case(
            When(blacklistedpaymentuser__isnull=False, then=False),
            default=True,
            output_field=BooleanField(),
        )

    def allow_tpay(self):
        """Give this user Thalia Pay permission."""
        BlacklistedPaymentUser.objects.filter(payment_user=self).delete()

    def disallow_tpay(self):
        """Revoke this user's Thalia Pay permission."""
        return BlacklistedPaymentUser.objects.get_or_create(payment_user=self)


class BlacklistedPaymentUser(models.Model):
    payment_user = models.OneToOneField(PaymentUser, on_delete=models.CASCADE,)

    def __str__(self):
        return f"{self.payment_user} (blacklisted from using Thalia Pay)"


class Payment(models.Model):
    """Describes a payment."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created_at = models.DateTimeField(_("created at"), default=timezone.now)

    CASH = "cash_payment"
    CARD = "card_payment"
    TPAY = "tpay_payment"
    WIRE = "wire_payment"

    PAYMENT_TYPE = (
        (CASH, _("Cash payment")),
        (CARD, _("Card payment")),
        (TPAY, _("Thalia Pay payment")),
        (WIRE, _("Wire payment")),
    )

    type = models.CharField(
        verbose_name=_("type"),
        blank=False,
        null=False,
        max_length=20,
        choices=PAYMENT_TYPE,
    )

    amount = models.DecimalField(
        verbose_name=_("amount"),
        blank=False,
        null=False,
        max_digits=5,
        decimal_places=2,
    )

    paid_by = models.ForeignKey(
        PaymentUser,
        models.CASCADE,
        verbose_name=_("paid by"),
        related_name="paid_payment_set",
        blank=False,
        null=True,
    )

    processed_by = models.ForeignKey(
        "members.Member",
        models.CASCADE,
        verbose_name=_("processed by"),
        related_name="processed_payment_set",
        blank=False,
        null=True,
    )

    batch = models.ForeignKey(
        "payments.Batch",
        models.PROTECT,
        related_name="payments_set",
        blank=True,
        null=True,
    )

    notes = models.TextField(verbose_name=_("notes"), blank=True, null=True)
    topic = models.CharField(verbose_name=_("topic"), max_length=255, default="Unknown")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # This is a pretty ugly hack, but it's necessary to something like this
        # when you want to check things against the old version of the model in
        # the clean() method---so some of the old data is saved here in init.

        # Previously we had something like this:
        # self._batch = self.batch
        # but this breaks when deleting the Payment instance, and creates a
        # stack overflow crash.

        # Instead we try to get the foreign key out of the init function arguments.
        # This works because when Django does database lookups via the .objects
        # manager, it uses the init method to create this model instance and it
        # includes the id. When we create a Payment in our own code we also use
        # this init method but use keyword arguments most of the time.

        # In the future we might want to remove this code and instead move
        # cleaning code to a place where we do have the old information available.
        self._batch_id = None
        if not kwargs:
            batch_id_idx = [
                i
                for i, x in enumerate(self._meta.concrete_fields)
                if x.attname == "batch_id"
            ]
            if (
                batch_id_idx
                and len(args) >= batch_id_idx[0]
                and args[batch_id_idx[0]] != DEFERRED
            ):
                self._batch_id = args[batch_id_idx[0]]
        else:
            # This should be okay as keyword arguments are only used for manual
            # instantiation.
            self._batch_id = self.batch_id

        self._type = self.type

    def save(self, **kwargs):
        self.clean()
        self._batch_id = self.batch.id if self.batch else None
        super().save(**kwargs)

    def clean(self):
        if self.amount == 0:
            raise ValidationError({"amount": _(f"Payments cannot be €{self.amount}")})
        if self.type != Payment.TPAY and self.batch is not None:
            raise ValidationError(
                {"batch": _("Non Thalia Pay payments cannot be added to a batch")}
            )
        if self._batch_id and Batch.objects.get(pk=self._batch_id).processed:
            raise ValidationError(
                _("Cannot change a payment that is part of a processed batch")
            )
        if self.batch and self.batch.processed:
            raise ValidationError(_("Cannot add a payment to a processed batch"))
        if (
            (self._state.adding or self._type != Payment.TPAY)
            and self.type == Payment.TPAY
            and not PaymentUser.objects.select_properties("tpay_enabled")
            .filter(pk=self.paid_by.pk, tpay_enabled=True)
            .exists()
        ):
            raise ValidationError(
                {"paid_by": _("This user does not have Thalia Pay enabled")}
            )

    def get_admin_url(self):
        content_type = ContentType.objects.get_for_model(self.__class__)
        return reverse(
            f"admin:{content_type.app_label}_{content_type.model}_change",
            args=(self.id,),
        )

    class Meta:
        verbose_name = _("payment")
        verbose_name_plural = _("payments")
        permissions = (("process_payments", _("Process payments")),)

    def __str__(self):
        return _("Payment of {amount:.2f}").format(amount=self.amount)


def _default_batch_description():
    now = timezone.now()
    return f"Thalia Pay payments for {now.year}-{now.month}"


def _default_withdrawal_date():
    return timezone.now() + settings.PAYMENT_BATCH_DEFAULT_WITHDRAWAL_DATE_OFFSET


class Batch(models.Model):
    """Describes a batch of payments for export."""

    processed = models.BooleanField(verbose_name=_("processing status"), default=False,)

    processing_date = models.DateTimeField(
        verbose_name=_("processing date"), blank=True, null=True,
    )

    description = models.TextField(
        verbose_name=_("description"), default=_default_batch_description,
    )

    withdrawal_date = models.DateField(
        verbose_name=_("withdrawal date"),
        null=False,
        blank=False,
        default=_default_withdrawal_date,
    )

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        if self.processed and not self.processing_date:
            self.processing_date = timezone.now()
        super().save(force_insert, force_update, using, update_fields)

    def get_absolute_url(self):
        return reverse("admin:payments_batch_change", args=[str(self.pk)])

    def start_date(self) -> datetime.datetime:
        return self.payments_set.earliest("created_at").created_at

    start_date.admin_order_field = "first payment in batch"
    start_date.short_description = _("first payment in batch")

    def end_date(self) -> datetime.datetime:
        return self.payments_set.latest("created_at").created_at

    end_date.admin_order_field = "last payment in batch"
    end_date.short_description = _("last payment in batch")

    def total_amount(self) -> Decimal:
        return sum([payment.amount for payment in self.payments_set.all()])

    total_amount.admin_order_field = "total amount"
    total_amount.short_description = _("total amount")

    def payments_count(self) -> Decimal:
        return self.payments_set.all().count()

    payments_count.admin_order_field = "payments count"
    payments_count.short_description = _("payments count")

    class Meta:
        verbose_name = _("batch")
        verbose_name_plural = _("batches")
        permissions = (("process_batches", _("Process batch")),)

    def __str__(self):
        return (
            f"{self.description} "
            f"({'processed' if self.processed else 'not processed'})"
        )


class BankAccount(models.Model):
    """Describes a bank account."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created_at = models.DateTimeField(_("created at"), default=timezone.now)

    last_used = models.DateField(verbose_name=_("last used"), blank=True, null=True,)

    owner = models.ForeignKey(
        to=PaymentUser,
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
        verbose_name=_("valid until"),
        blank=True,
        null=True,
        help_text=_(
            "Users can revoke the mandate at any time, as long as they do not have any Thalia Pay payments that have not been processed. If you revoke a mandate, make sure to check that all unprocessed Thalia Pay payments are paid in an alternative manner."
        ),
    )

    signature = models.TextField(verbose_name=_("signature"), blank=True, null=True,)

    MANDATE_NO_DEFAULT_REGEX = r"^\d+-\d+$"
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
                        {field[0]: _("This field is required to complete the mandate.")}
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
    def can_be_revoked(self):
        return not self.owner.paid_payment_set.filter(
            (Q(batch__isnull=True) | Q(batch__processed=False)) & Q(type=Payment.TPAY)
        ).exists()

    @property
    def valid(self):
        if self.valid_from is not None and self.valid_until is not None:
            return self.valid_from <= timezone.now().date() < self.valid_until
        return self.valid_from is not None and self.valid_from <= timezone.now().date()

    def __str__(self):
        return f"{self.iban} - {self.name}"

    class Meta:
        ordering = ("created_at",)
