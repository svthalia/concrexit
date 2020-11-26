from django.db import models

from sales.models.product_list import ProductList


class Shift(models.Model):
    start_date = models.DateTimeField(blank=False, null=False,)
    end_date = models.DateTimeField(blank=False, null=False,)

    product_list = models.ForeignKey(ProductList, blank=False, null=False, on_delete=models.PROTECT)

    def __str__(self):
        return f"Shift {self.id} from {self.start_date} until {self.end_date}"
