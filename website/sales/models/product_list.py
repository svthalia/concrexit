from _decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import models

from sales.models.product import Product


class ProductList(models.Model):
    """A list of products with various prices."""

    name = models.CharField(max_length=50, unique=True, null=False, blank=False)
    products = models.ManyToManyField(Product, related_name='items', through='ProductListItem')

    def __str__(self):
        return self.name

class ProductListItem(models.Model):
    product = models.ForeignKey(Product, null=False, blank=False, on_delete=models.CASCADE)
    product_list = models.ForeignKey(ProductList, null=False, blank=False, on_delete=models.CASCADE)
    price = models.DecimalField(
        max_digits=6, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))]
    )

    def __str__(self):
        return f"{self.product} ({self.product_list.name}) - €{self.price}"
