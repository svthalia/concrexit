from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import (
    Sum,
    Q,
    Count,
)
from django.db.models.expressions import RawSQL
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from queryable_properties.managers import QueryablePropertiesManager
from queryable_properties.properties import (
    RangeCheckProperty,
    queryable_property,
)

from activemembers.models import MemberGroup
from sales.models.product import ProductList


class Shift(models.Model):
    class Meta:
        permissions = [
            ("override_manager", _("Can access all shifts as manager")),
        ]

    objects = QueryablePropertiesManager()

    start = models.DateTimeField(verbose_name=_("start"), blank=False, null=False,)
    end = models.DateTimeField(
        verbose_name=_("end"),
        blank=False,
        null=False,
        help_text=_(
            "The end time is only indicative and does not prevent orders being created after the shift has ended. This only happens after locking the shift."
        ),
    )

    title = models.CharField(
        verbose_name=_("title"), blank=True, null=True, max_length=100
    )

    product_list = models.ForeignKey(
        ProductList,
        verbose_name=_("product list"),
        blank=False,
        null=False,
        on_delete=models.PROTECT,
    )

    managers = models.ManyToManyField(
        MemberGroup, verbose_name=_("managers"), related_name="manager_shifts"
    )

    locked = models.BooleanField(
        verbose_name=_("locked"),
        blank=False,
        null=False,
        default=False,
        help_text=_(
            "Prevent orders being changed or created for this shift. This will also clean up all unpaid orders in this shift."
        ),
    )

    def clean(self):
        super().clean()
        errors = {}

        if self.orders.filter(created_at__lt=self.start):
            errors.update(
                {
                    "start": _(
                        "There are already orders created in this shift before this start time."
                    )
                }
            )

        if self.end and self.start and self.end <= self.start:
            errors.update({"end": _("End cannot be before start.")})

        if errors:
            raise ValidationError(errors)

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        if self.locked:
            self.orders.filter(
                (Q(payment__isnull=True) & Q(total_amount__gt=0))
                | Q(order_items__isnull=True)
            ).delete()

        return super(Shift, self).save(force_insert, force_update, using, update_fields)

    active = RangeCheckProperty("start", "end", timezone.now)

    @queryable_property(annotation_based=True)
    @classmethod
    def total_revenue(cls):
        return RawSQL(
            """(SELECT CAST(COALESCE(SUM("__orders"."total__"), 0) AS NUMERIC) AS "shift_revenue__"
                FROM (
                    SELECT "sales_order"."id", "sales_order"."shift_id", "sales_order"."discount", "sales_order"."payment_id", CAST(SUM("sales_orderitem"."total") AS NUMERIC) AS "subtotal__", CAST((SUM("sales_orderitem"."total") - COALESCE("sales_order"."discount", 0)) AS NUMERIC) AS "total__", SUM("sales_orderitem"."amount") AS "num_items__"
                    FROM "sales_order" LEFT JOIN "sales_orderitem" ON "sales_orderitem"."order_id" = "sales_order"."id"
                    GROUP BY "sales_order"."id", "sales_order"."shift_id", "sales_order"."discount"
                    ) AS "__orders"
                WHERE "__orders"."shift_id"="sales_shift"."id"
                )""",
            [],
        )

    @queryable_property(annotation_based=True)
    @classmethod
    def total_revenue_paid(cls):
        return RawSQL(
            """(SELECT CAST(COALESCE(SUM("__orders"."total__"), 0) AS NUMERIC) AS "shift_revenue__"
                FROM (
                    SELECT "sales_order"."id", "sales_order"."shift_id", "sales_order"."discount", "sales_order"."payment_id", CAST(SUM("sales_orderitem"."total") AS NUMERIC) AS "subtotal__", CAST((SUM("sales_orderitem"."total") - COALESCE("sales_order"."discount", 0)) AS NUMERIC) AS "total__", SUM("sales_orderitem"."amount") AS "num_items__"
                    FROM "sales_order" LEFT JOIN "sales_orderitem" ON "sales_orderitem"."order_id" = "sales_order"."id"
                    GROUP BY "sales_order"."id", "sales_order"."shift_id", "sales_order"."discount"
                    ) AS "__orders"
                WHERE "__orders"."shift_id"="sales_shift"."id"
                AND ("__orders"."payment_id" IS NOT NULL OR ("__orders"."payment_id" IS NULL AND "__orders"."total__"=0))
                )""",
            [],
        )

    @queryable_property(annotation_based=True)
    @classmethod
    def num_orders(cls):
        return Count("orders")

    @queryable_property(annotation_based=True)
    @classmethod
    def num_orders_paid(cls):
        return RawSQL(
            """(SELECT COUNT(*) AS "num_orders__"
                FROM (
                    SELECT "sales_order"."id", "sales_order"."shift_id", "sales_order"."discount", "sales_order"."payment_id", CAST(SUM("sales_orderitem"."total") AS NUMERIC) AS "subtotal__", CAST((SUM("sales_orderitem"."total") - COALESCE("sales_order"."discount", 0)) AS NUMERIC) AS "total__", SUM("sales_orderitem"."amount") AS "num_items__"
                    FROM "sales_order" LEFT JOIN "sales_orderitem" ON "sales_orderitem"."order_id" = "sales_order"."id"
                    GROUP BY "sales_order"."id", "sales_order"."shift_id", "sales_order"."discount"
                    ) AS "__orders"
                WHERE "__orders"."shift_id"="sales_shift"."id"
                AND ("__orders"."payment_id" IS NOT NULL OR ("__orders"."payment_id" IS NULL AND "__orders"."total__"=0))
                )""",
            [],
        )

    @property
    def product_sales(self):
        qs = (
            self.orders.exclude(order_items__isnull=True)
            .values("order_items__product")
            .annotate(sold=Sum("order_items__amount"))
            .order_by()
        )
        return {
            item[0]: item[1]
            for item in qs.values_list("order_items__product__product__name", "sold")
        }

    def __str__(self):
        if self.title and self.title != "":
            return f"Shift {self.pk} - {self.title}"
        return f"Shift {self.pk}"
