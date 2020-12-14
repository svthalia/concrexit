from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from sales.models.product import ProductList


class Shift(models.Model):
    start_date = models.DateTimeField(blank=False, null=False,)
    end_date = models.DateTimeField(blank=False, null=False,)

    product_list = models.ForeignKey(
        ProductList, blank=False, null=False, on_delete=models.PROTECT
    )

    def __str__(self):
        return f"Shift {self.id} from {self.start_date} until {self.end_date}"

    def clean(self):
        super().clean()
        errors = {}

        if self.end_date <= self.start_date:
            errors.update({"end_date": _("End cannot be before start.")})

        if errors:
            raise ValidationError(errors)

    @property
    def total_revenue(self):
        return sum([x.total_amount for x in self.orders.all()])

    @property
    def is_active(self):
        return self.start_date <= timezone.now() <= self.end_date

    @staticmethod
    def currently_active():
        return Shift.objects.filter(
            start_date__lte=timezone.now(), end_date__gte=timezone.now()
        )
