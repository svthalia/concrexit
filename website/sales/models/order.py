from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from members.models import uuid
from payments.models import Payable, Payment
from sales.models.product_list import ProductListItem
from sales.models.shift import Shift


class Order(models.Model, Payable):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created_at = models.DateTimeField(default=timezone.now)

    shift = models.ForeignKey(Shift, related_name='orders', null=False, blank=False, on_delete=models.PROTECT)

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

        if self.discount and self.discount > self.total_amount:
            errors.update(
                {"discount": _("Discount cannot be higher than total amount.")}
            )

        if errors:
            raise ValidationError(errors)

    @property
    def total_amount(self):
        return sum([x.total_price for x in self.orderitem_set.all()])

    @property
    def payment_amount(self):
        return self.total_amount - self.discount if self.discount else self.total_amount

    @property
    def payment_topic(self):
        return f"Sales at {self.shift}"

    @property
    def payment_notes(self):
        return f"{','.join(str(x) for x in self.orderitem_set.all())}. Ordered at {self.created_at.time()} ({self.id})"

    @property
    def payment_payer(self):
        return None

    def __str__(self):
        return f"Order {self.id} ({self.created_at})"


    # TODO if a payment is added, this cannot be altered anymore

class OrderItem(models.Model):
    product = models.ForeignKey(ProductListItem, null=False, blank=False, on_delete=models.PROTECT)
    order = models.ForeignKey(Order, null=False, blank=False, on_delete=models.CASCADE)
    amount = models.PositiveSmallIntegerField(null=False, blank=False)

    @property
    def total_price(self):
        return self.amount * self.product.price

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
