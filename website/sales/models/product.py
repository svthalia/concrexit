from django.core.validators import MinValueValidator
from django.db import models

from django.utils.translation import gettext_lazy as _

from payments.models import PaymentAmountField


class Product(models.Model):
    """Products that can be ordered."""

    name = models.CharField(
        verbose_name=_("name"), max_length=50, unique=True, null=False, blank=False
    )
    age_restricted = models.BooleanField(
        verbose_name=_("age restricted"), default=False, null=False, blank=False
    )

    def __str__(self):
        return self.name

    class Meta:
        """Meta class."""

        verbose_name = _("product")
        verbose_name_plural = _("products")
        ordering = ["name"]


class ProductList(models.Model):
    """A list of products with various prices."""

    class Meta:
        verbose_name = _("product list")
        verbose_name_plural = _("product lists")

    name = models.CharField(
        verbose_name=_("name"), max_length=50, unique=True, null=False, blank=False
    )
    products = models.ManyToManyField(
        Product, verbose_name=_("products"), through="ProductListItem"
    )

    def __str__(self):
        return self.name


class ProductListItem(models.Model):
    class Meta:
        verbose_name = _("product")
        verbose_name_plural = _("products")

    product = models.ForeignKey(
        Product,
        verbose_name=_("product"),
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )
    product_list = models.ForeignKey(
        ProductList,
        verbose_name=_("product list"),
        related_name="product_items",
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )
    price = PaymentAmountField(
        verbose_name=_("price"), allow_zero=True, validators=[MinValueValidator(0)],
    )

    def __str__(self):
        return f"{self.product} ({self.price})"

    @property
    def product_name(self):
        return self.product.name
