"""Registers admin interfaces for the models defined in this module."""
import csv

from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.utils.html import format_html
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _

from moneybirdsynchronization import services as moneybird_services
from payments import services as payment_services
from payments.models import Payment, PaymentUser

from .models import MerchandiseItem, MerchandiseSale, MerchandiseSaleItem


class MerchandiseSaleInline(admin.TabularInline):
    """Inline for merchandise sales."""

    model = MerchandiseSaleItem
    extra = 0

    fields = ("item", "amount", "total", "purchase_total",)
    autocomplete_fields = ("item",)
    readonly_fields = ("total","purchase_total",)

    def get_readonly_fields(self, request: HttpRequest, obj: MerchandiseSale = None):
        if not obj:
            return ("total","purchase_total",)
        if obj.payment:
            return (
                "item",
                "amount",
                "total",
                "purchase_total",
            )
        return super().get_readonly_fields(request, obj)

    def has_delete_permission(self, request, obj=None):
        if isinstance(obj, MerchandiseSale):
            if obj.payment:
                return False

        return super().has_delete_permission(request, obj)

    def has_add_permission(self, request, obj=None):
        if isinstance(obj, MerchandiseSale):
            if obj.payment:
                return False

        return super().has_add_permission(request, obj)


@admin.register(MerchandiseItem)
class MerchandiseItemAdmin(ModelAdmin):
    """This manages the admin interface for the model items."""

    #: Included fields in the admin interface
    fields = (
        "name",
        "price",
        "purchase_price",
        "description",
        "image",
    )
    search_fields = ("name", "description")


@admin.register(MerchandiseSale)
class MerchandiseSaleAdmin(admin.ModelAdmin):
    """Manage the merch payments."""

    inlines = [MerchandiseSaleInline]
    list_display = (
        "created_at",
        "paid_by_link",
        "total_amount",
        "total_purchase_amount",
        "type",
        "payment_link",
    )
    list_filter = ["type"]
    date_hierarchy = "created_at"
    fields = (
        "created_at",
        "paid_by",
        "type",
        "payment",
        "total_amount",
        "total_purchase_amount",
        "notes",
    )
    readonly_fields = (
        "created_at",
        "paid_by",
        "total_amount",
        "total_purchase_amount",
        "type",
        "payment",
        "notes",
    )
    search_fields = (
        "items__item__name",
        "paid_by__username",
        "paid_by__first_name",
        "paid_by__last_name",
        "notes",
        "total_amount",
        "total_purchase_amount",
    )
    ordering = ("-created_at",)
    autocomplete_fields = ("paid_by",)
    actions = [
        "export_csv",
    ]

    @staticmethod
    def _member_link(member: PaymentUser) -> str:
        return (
            format_html(
                "<a href='{}'>{}</a>", member.get_absolute_url(), member.get_full_name()
            )
            if member
            else None
        )

    def paid_by_link(self, obj: MerchandiseSale) -> str:
        return self._member_link(obj.paid_by)

    paid_by_link.admin_order_field = "paid_by"
    paid_by_link.short_description = _("paid by")

    @staticmethod
    def _payment_link(payment: Payment) -> str:
        if payment:
            return format_html(
                "<a href='{}'>{}</a>", payment.get_admin_url(), str(payment)
            )

    def payment_link(self, obj: MerchandiseSale) -> str:
        if obj.payment:
            return self._payment_link(obj.payment)
        return None

    payment_link.admin_order_field = "payment"
    payment_link.short_description = _("payment")

    def has_delete_permission(self, request, obj=None):
        if isinstance(obj, MerchandiseSale):
            if obj.payment.batch and obj.payment.batch.processed:
                return False
        if (
            "merchandisesale/" in request.path
            and request.POST
            and request.POST.get("action") == "delete_selected"
        ):
            for sale_id in request.POST.getlist("_selected_action"):
                sale = MerchandiseSale.objects.get(id=sale_id)
                if sale.payment.batch and sale.payment.batch.processed:
                    return False

        return super().has_delete_permission(request, obj)

    def get_readonly_fields(self, request: HttpRequest, obj: MerchandiseSale = None):
        if not obj:
            return "created_at", "total_amount", "total_purchase_amount", "payment"
        if obj.payment:
            return (
                "created_at",
                "paid_by",
                "total_amount",
                "total_purchase_amount",
                "type",
                "payment",
                "notes",
            )
        return super().get_readonly_fields(request, obj)

    def save_related(self, request, form, formsets, change):
        obj = form.instance
        for formset in formsets:
            formset.save()
            total_amount = sum([item.total for item in obj.sale_items.all()])
            obj.total_amount = total_amount
            total_purchase_amount = sum([item.purchase_total for item in obj.sale_items.all()])
            obj.total_purchase_amount = total_purchase_amount
            obj.save()

            obj.payment = payment_services.create_payment(
                model_payable=obj, processed_by=request.user, pay_type=obj.type
            )
            obj.save()
            moneybird_services.create_or_update_merchandise_sale(obj)

        super().save_related(request, form, formsets, change)

    def export_csv(self, request: HttpRequest, queryset: QuerySet) -> HttpResponse:
        """Export a CSV of payments.

        :param request: Request
        :param queryset: Items to be exported
        """
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment;filename="merchandise_sales.csv"'
        writer = csv.writer(response)
        headers = [
            _("created"),
            _("payer id"),
            _("payer name"),
            _("total_amount"),
            _("total_purchase_amount"),
            _("type"),
            _("notes"),
        ]
        writer.writerow([capfirst(x) for x in headers])
        for sale in queryset:
            writer.writerow(
                [
                    sale.created_at,
                    sale.paid_by.pk if sale.paid_by else "-",
                    sale.paid_by.get_full_name() if sale.paid_by else "-",
                    sale.total_amount,
                    sale.total_purchase_amount
                    sale.get_type_display(),
                    sale.notes,
                ]
            )
        return response

    export_csv.short_description = _("Export")
