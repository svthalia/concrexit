"""Models for the merchandise database tables."""
import uuid

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from queryable_properties.managers import QueryablePropertiesManager
from thumbnails.fields import ImageField

from members.models import Member
from payments.models import Payment, PaymentAmountField
from thaliawebsite.storage.backend import get_public_storage


class MerchandiseItem(models.Model):
    """Merchandise items.

    This model describes merchandise items.
    """

    #: Name of the merchandise item.
    name = models.CharField(max_length=200)

    #: Price of the merchandise item
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
    )

    #: Purchase price of the merchandise item
    purchase_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
    )

    #: Description of the merchandise item
    description = models.TextField()

    #: Image of the merchandise item
    image = ImageField(
        upload_to="merchandise",
        storage=get_public_storage,
        resize_source_to="source",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.image:
            self._orig_image = self.image.name
        else:
            self._orig_image = None

    def delete(self, using=None, keep_parents=False):
        if self.image.name:
            self.image.delete()
        return super().delete(using, keep_parents)

    def save(self, **kwargs):
        super().save(**kwargs)
        storage = self.image.storage

        if self._orig_image and self._orig_image != self.image.name:
            storage.delete(self._orig_image)
            self._orig_image = None

    def __str__(self):
        """Give the name of the merchandise item in the currently active locale.

        :return: The name of the merchandise item.
        :rtype: str
        """
        return str(self.name)


class MerchandiseSale(models.Model):
    """Describes a merchandise sale."""

    objects = QueryablePropertiesManager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created_at = models.DateTimeField(_("created at"), default=timezone.now)

    items = models.ManyToManyField(
        MerchandiseItem,
        through="MerchandiseSaleItem",
        verbose_name=_("items"),
    )

    paid_by = models.ForeignKey(
        Member,
        models.PROTECT,
        verbose_name=_("paid by"),
        related_name="merchandise_sale_set",
        blank=False,
        null=True,
    )

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

    payment = models.OneToOneField(
        Payment,
        models.CASCADE,
        verbose_name=_("payment"),
        related_name="merchandise_sale_set",
        blank=True,
        null=True,
    )

    total_amount = PaymentAmountField(
        allow_zero=True, verbose_name=_("total amount"), null=True
    )

    total_purchase_amount = PaymentAmountField(
        allow_zero=True, verbose_name=_("total purchase amount"), null=True
    )


    notes = models.TextField(verbose_name=_("notes"), blank=True, null=True)

    @property
    def sale_description(self):
        return "Merchandise sale:" + ", ".join(
            [str(item.amount) + "x " + str(item.item) for item in self.sale_items.all()]
        )

    def get_absolute_url(self):
        return reverse("admin:merchandise_sales_change", args=[str(self.pk)])

    class Meta:
        verbose_name = _("merchandise sale")
        verbose_name_plural = _("merchandise sales")

    def __str__(self):
        return _("Merchandise sale of {total_amount}").format(
            total_amount=self.total_amount
        )


class MerchandiseSaleItem(models.Model):
    """Describes a merchandise sale item."""

    sale = models.ForeignKey(
        MerchandiseSale,
        models.CASCADE,
        verbose_name=_("sale"),
        related_name="sale_items",
        blank=False,
        null=True,
    )

    item = models.ForeignKey(
        MerchandiseItem,
        models.PROTECT,
        verbose_name=_("item"),
        related_name="item_merchandise_sale_item_set",
        blank=True,
        null=True,
    )

    amount = models.PositiveSmallIntegerField(
        verbose_name=_("amount"),
        default=1,
        blank=False,
        null=True,
    )

    total = PaymentAmountField(
        verbose_name=_("total"),
        allow_zero=False,
        blank=False,
        null=True,
    )

    purchase_total = PaymentAmountField(
        verbose_name=_("purchase total"),
        allow_zero=False,
        blank=False,
        null=True,
    )


    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        if self.amount == 0:
            if self.pk:
                self.delete()
            else:
                return

        self.total = self.item.price * self.amount
        self.purchase_total = self.item.purchase_price * self.amount

        super().save(force_insert, force_update, using, update_fields)
        self.sale.save()

    def __str__(self):
        return str(self.sale)

    class Meta:
        verbose_name = _("sale item")
        verbose_name_plural = _("sale items")

    def delete(self, using=None, keep_parents=False):
        super().delete(using, keep_parents)
        self.sale.save()
