from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import (
    Sum,
    Value,
    F,
    DecimalField,
    Q,
    IntegerField,
    BooleanField,
    Count,
)
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from queryable_properties.managers import QueryablePropertiesManager
from queryable_properties.properties import AnnotationProperty

from members.models import uuid, Member
from payments.models import Payment
from sales.models.product import ProductListItem
from sales.models.shift import Shift


def default_order_shift():
    return Shift.objects.filter(active=True).first()


class Order(models.Model):

    objects = QueryablePropertiesManager()

    class Meta:
        verbose_name = _("order")
        verbose_name_plural = _("orders")
        permissions = [
            ("custom_prices", _("Can use custom prices and discounts in orders")),
        ]
        ordering = ["created_at"]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created_at = models.DateTimeField(
        verbose_name=_("created at"), default=timezone.now
    )

    shift = models.ForeignKey(
        Shift,
        verbose_name=_("shift"),
        related_name="orders",
        default=default_order_shift,
        null=False,
        blank=False,
        on_delete=models.PROTECT,
    )

    items = models.ManyToManyField(
        ProductListItem, through="OrderItem", verbose_name=_("items"),
    )

    payment = models.OneToOneField(
        Payment,
        verbose_name=_("payment"),
        related_name="sales_order",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    discount = models.DecimalField(
        verbose_name=_("discount"),
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    payer = models.ForeignKey(
        Member,
        models.SET_NULL,
        verbose_name=_("payer"),
        related_name="sales_order",
        blank=True,
        null=True,
    )

    age_restricted = AnnotationProperty(
        Count(
            "order_items__pk",
            filter=Q(order_items__product__product__age_restricted=True),
            output_field=BooleanField(),
        )
    )

    subtotal = AnnotationProperty(
        Coalesce(Sum("order_items__total"), Value(0.00), output_field=DecimalField())
    )

    total_amount = AnnotationProperty(
        Coalesce(Sum("order_items__total"), Value(0.00), output_field=DecimalField())
        - Coalesce(F("discount"), Value(0.00), output_field=DecimalField())
    )

    num_items = AnnotationProperty(
        Coalesce(Sum("order_items__amount"), Value(0), output_field=IntegerField())
    )

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        if self.shift.locked:
            raise ValueError("The shift this order belongs to is locked.")
        if self.shift.start > timezone.now():
            raise ValueError("The shift hasn't started yet.")
        if (
            self.payment
            and self.subtotal - Decimal(self.discount or 0) != self.payment.amount
        ):
            # We cannot use self.total_amount as it is a requires a database query and hence will not use any updated values
            raise ValueError(
                "The payment amount does not match the order total amount."
            )
        if self.payment and not self.payer:
            self.payer = self.payment.paid_by

        return super(Order, self).save(force_insert, force_update, using, update_fields)

    def clean(self):
        super().clean()
        errors = {}

        if self.shift.start > timezone.now():
            errors.update({"shift": _("The shift hasn't started yet.")})

        if self.shift.locked:
            errors.update({"shift": _("The shift this order belongs to is locked.")})

        if self.discount and self.discount > self.total_amount:
            errors.update(
                {"discount": _("Discount cannot be higher than total amount.")}
            )

        if errors:
            raise ValidationError(errors)

    @property
    def order_description(self):
        return ", ".join(str(x) for x in self.order_items.all())

    @property
    def accept_payment_from_any_user(self):
        return True

    @property
    def payment_url(self):
        return (
            settings.BASE_URL + reverse("sales:order-pay", kwargs={"pk": self.pk})
            if not self.payment
            else None
        )

    def __str__(self):
        return f"Order {self.id} ({self.shift})"


class OrderItem(models.Model):
    class Meta:
        verbose_name = "item"
        verbose_name_plural = "items"
        ordering = ["pk"]
        indexes = [
            models.Index(fields=["order"]),
        ]

    product = models.ForeignKey(
        ProductListItem,
        verbose_name=_("product"),
        null=False,
        blank=False,
        on_delete=models.PROTECT,
    )
    order = models.ForeignKey(
        Order,
        verbose_name=_("order"),
        related_name="order_items",
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )
    total = models.DecimalField(
        verbose_name=_("total"),
        max_digits=6,
        decimal_places=2,
        null=False,
        blank=True,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Only when overriding the default",
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name=_("amount"), null=False, blank=False
    )

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        if self.order.shift.locked:
            raise ValueError("The shift this order belongs to is locked.")
        if self.order.payment:
            raise ValueError("This order has already been paid for.")

        if not self.total:
            self.total = self.product.price * self.amount

        return super(OrderItem, self).save(
            force_insert, force_update, using, update_fields
        )

    def clean(self):
        super().clean()
        errors = {}

        if self.order.shift.locked:
            errors.update({"order": _("The shift is locked.")})

        if self.product not in self.order.shift.product_list.product_items.all():
            errors.update({"product": _("This product is not available.")})

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.amount}x {self.product.product.name}"
