from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from pylint.checkers.typecheck import _

from members.models import uuid
from payments.models import Payable, Payment
from sales.models.product_list import ProductListItem
from sales.models.shift import Shift


def default_order_shift():
    return Shift.currently_active().first()

class Order(models.Model, Payable):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created_at = models.DateTimeField(default=timezone.now)

    shift = models.ForeignKey(Shift, related_name='orders', default=default_order_shift, null=False, blank=False, on_delete=models.PROTECT)

    items = models.ManyToManyField(ProductListItem, through='OrderItem')

    payment = models.OneToOneField(Payment,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    discount = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(Decimal("0.00"))]
    )

    def clean(self):
        super().clean()
        errors = {}

        # TODO prevent changing orders when they are paid

        if self.discount and self.discount > self.total_amount:
            errors.update(
                {"discount": _("Discount cannot be higher than total amount.")}
            )

        if errors:
            raise ValidationError(errors)

    @property
    def age_restricted(self):
        return any(self.orderitem_set.values_list('product__product__age_restricted', flat=True))

    @property
    def total_amount(self):
        return sum([x.total for x in self.orderitem_set.all()])

    @property
    def payment_amount(self):
        return self.total_amount - self.discount if self.discount else self.total_amount

    @property
    def payment_topic(self):
        return f"Sales at {self.shift}"

    @property
    def order_description(self):
        return ', '.join(str(x) for x in self.orderitem_set.all())

    @property
    def payment_notes(self):
        return f"{self.order_description}. Ordered at {self.created_at.time()} ({self.id})"

    @property
    def payment_payer(self):
        return None

    @property
    def ordered_by(self):
        return self.payment.paid_by if self.payment else None

    def __str__(self):
        return f"Order {self.id} ({self.created_at})"


class OrderItem(models.Model):
    product = models.ForeignKey(ProductListItem, null=False, blank=False, on_delete=models.PROTECT)
    order = models.ForeignKey(Order, null=False, blank=False, on_delete=models.CASCADE)
    total = models.DecimalField(
        max_digits=6, decimal_places=2, null=False, blank=True,
        validators=[MinValueValidator(Decimal("0.00"))], help_text="Only when overriding the default"
    )
    amount = models.PositiveSmallIntegerField(null=False, blank=False)


    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if not self.total:
            self.total = self.product.price * self.amount
        return super(OrderItem, self).save(force_insert, force_update, using, update_fields)

    def clean(self):
        super().clean()
        errors = {}

        if self.product not in self.order.shift.product_list.productlistitem_set.all():
            errors.update(
                {"product": _("This product is not available.")}
            )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.amount}x {self.product.product.name}"
