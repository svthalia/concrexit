from django.contrib import admin, messages
from django.contrib.admin import register

from django.utils.translation import gettext_lazy as _

from sales.models.order import Order
from sales.models.shift import Shift, SelfOrderPeriod
from sales.services import is_manager


class SelfOrderPeriodInline(admin.TabularInline):
    model = SelfOrderPeriod
    ordering = ("start",)
    extra = 0
    fields = (
        "start",
        "end",
        "product_list",
    )

    def has_change_permission(self, request, obj=None):
        if obj and obj.locked:
            return False
        if obj and not is_manager(request.member, obj):
            return False
        return super().has_change_permission(request, obj)


class OrderInline(admin.TabularInline):
    model = Order
    ordering = ("created_at",)
    extra = 0
    show_change_link = True
    can_delete = False

    fields = (
        "created_at",
        "id",
        "order_description",
        "discount",
        "total_amount",
        "paid",
        "payer",
    )

    readonly_fields = (
        "created_at",
        "id",
        "order_description",
        "discount",
        "total_amount",
        "paid",
        "payer",
    )

    def has_add_permission(self, request, obj):
        return False

    def has_change_permission(self, request, obj=None):
        if obj and obj.locked:
            return False

        if obj and not is_manager(request.member, obj):
            return False

        return super().has_change_permission(request, obj)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_properties(
            "total_amount", "subtotal", "num_items", "age_restricted"
        )
        queryset = queryset.prefetch_related("payment")
        queryset = queryset.prefetch_related("order_items__product__product")
        queryset = queryset.prefetch_related("payer")
        return queryset

    def total_amount(self, obj):
        if obj.total_amount:
            return f"€{obj.total_amount:.2f}"
        return "-"

    def discount(self, obj):
        if obj.discount:
            return f"€{obj.discount:.2f}"
        return "-"

    def paid(self, obj):
        if obj.total_amount is None or obj.total_amount == 0:
            return None
        return obj.payment is not None

    paid.boolean = True


@register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    inlines = [
        SelfOrderPeriodInline,
        OrderInline,
    ]
    search_fields = (
        "id",
        "title",
        "start",
        "end",
    )
    filter_horizontal = ("managers",)
    date_hierarchy = "start"
    list_display_links = (
        "id",
        "title",
    )
    list_display = (
        "id",
        "title",
        "start",
        "end",
        "active",
        "locked",
        "product_list",
        "num_orders",
        "total_revenue",
    )
    fields = (
        "title",
        "start",
        "end",
        "active",
        "product_list",
        "managers",
        "product_sales",
        "num_orders",
        "total_revenue",
        "locked",
    )

    readonly_fields = (
        "active",
        "total_revenue",
        "num_orders",
        "product_sales",
    )

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        if not obj:
            fields += ("locked",)
        return fields

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        if not request.member:
            queryset = queryset.none()
        elif not request.member.has_perm("sales.override_manager"):
            queryset = queryset.filter(
                managers__in=request.member.get_member_groups()
            ).distinct()

        queryset = queryset.select_properties(
            "active",
            "total_revenue",
            "total_revenue_paid",
            "num_orders",
            "num_orders_paid",
        )
        queryset = queryset.prefetch_related("event")
        return queryset

    def has_view_permission(self, request, obj=None):
        if obj and not is_manager(request.member, obj):
            return False
        return super().has_view_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        if obj and obj.locked:
            return False
        if obj and not is_manager(request.member, obj):
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.locked:
            return False
        if obj and not is_manager(request.member, obj):
            return False
        return super().has_delete_permission(request, obj)

    def changelist_view(self, request, extra_context=None):
        if not (request.member and request.member.has_perm("sales.override_manager")):
            self.message_user(
                request,
                _("You are only seeing shifts that you are managing."),
                messages.WARNING,
            )
        return super().changelist_view(request, extra_context)

    def active(self, obj):
        return obj.active

    active.boolean = True

    def num_orders(self, obj):
        if obj.num_orders and obj.num_orders != obj.num_orders_paid:
            return f"{obj.num_orders} ({obj.num_orders - obj.num_orders_paid} {_('unpaid')})"
        return obj.num_orders

    def total_revenue(self, obj):
        if obj.total_revenue and obj.total_revenue != obj.total_revenue_paid:
            return f"€{obj.total_revenue:.2f} (€{obj.total_revenue-obj.total_revenue_paid:.2f} {_('unpaid')})"
        return f"€{obj.total_revenue:.2f}"

    def product_sales(self, obj):
        output = "\n".join(f"- {str(k)}: {v}x" for k, v in obj.product_sales.items())
        if obj.num_orders != obj.num_orders_paid:
            return f"{output}\n{_('This includes some orders that are unpaid.')}"
        return output
