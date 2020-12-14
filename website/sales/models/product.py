from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class Product(models.Model):
    """Products that can be ordered."""

    name = models.CharField(max_length=50, unique=True, null=False, blank=False)
    age_restricted = models.BooleanField(default=False, null=False, blank=False)

    def __str__(self):
        return self.name

    class Meta:
        """Meta class."""

        verbose_name = "product "
        verbose_name_plural = "products"
        ordering = ["name"]


class ProductList(models.Model):
    """A list of products with various prices."""

    class Meta:
        verbose_name = "product list"
        verbose_name_plural = "product lists"

    name = models.CharField(max_length=50, unique=True, null=False, blank=False)
    products = models.ManyToManyField(
        Product, related_name="items", through="ProductListItem"
    )

    def __str__(self):
        return self.name


class ProductListItem(models.Model):
    class Meta:
        verbose_name = "product"
        verbose_name_plural = "products"

    product = models.ForeignKey(
        Product, null=False, blank=False, on_delete=models.CASCADE
    )
    product_list = models.ForeignKey(
        ProductList, null=False, blank=False, on_delete=models.CASCADE
    )
    price = models.DecimalField(
        max_digits=6, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))]
    )

    def __str__(self):
        return f"{self.product} ({self.price})"
