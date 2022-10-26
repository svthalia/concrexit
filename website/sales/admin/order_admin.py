from functools import partial

from django.contrib import admin, messages
from django.contrib.admin import SimpleListFilter, register
from django.forms import Field
from django.http import HttpRequest
from django.urls import resolve
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from admin_auto_filters.filters import AutocompleteFilter

from payments.widgets import PaymentWidget
from sales import services
from sales.models.order import Order, OrderItem
from sales.models.shift import Shift
from sales.services import is_manager


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1

    fields = ("product", "product_name", "amount", "total")
    readonly_fields = ("product_name",)

    def get_readonly_fields(self, request: HttpRequest, obj: Order = None):
        default_fields = self.readonly_fields

        if not (request.member and request.member.has_perm("sales.custom_prices")):
            default_fields += ("total",)

        return default_fields

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.prefetch_related("product", "product__product")
        return queryset

    def has_add_permission(self, request, obj):
        if obj and obj.shift.locked:
            return False

        if obj and obj.payment:
            return False

        parent = self.get_parent_object_from_request(request)
        if not parent:
            return False

        return super().has_add_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        if obj and obj.payment:
            return False
        if obj and obj.shift.locked:
            return False
        if obj and not is_manager(request.member, obj.shift):
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        if obj and obj.payment:
            return False
        if obj and obj.shift.locked:
            return False
        if obj and not is_manager(request.member, obj.shift):
            return False
        return True

    def get_parent_object_from_request(self, request):
        """Get parent object to determine product list."""
        resolved = resolve(request.path_info)
        if resolved.kwargs:
            parent = self.parent_model.objects.get(pk=resolved.kwargs["object_id"])
            return parent
        return None

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        """Limit product list items to items of order's shift."""
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)

        if db_field.name == "product":
            if request is not None:
                parent = self.get_parent_object_from_request(request)
                if parent:
                    field.queryset = parent.shift.product_list.product_items
            else:
                field.queryset = field.queryset.none()

        return field


class OrderShiftFilter(AutocompleteFilter):
    title = _("shift")
    field_name = "shift"
    rel_model = Order

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(shift=self.value())
        return queryset


class OrderMemberFilter(AutocompleteFilter):
    title = _("member")
    field_name = "payer"
    rel_model = Order

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(payer=self.value())
        return queryset


class OrderPaymentFilter(SimpleListFilter):
    title = _("payment")
    parameter_name = "payment"

    def lookups(self, request, model_admin):
        return (
            ("not_required", _("No payment required")),
            ("paid", _("Paid")),
            ("unpaid", _("Unpaid")),
        )

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        if self.value() == "paid":
            return queryset.filter(payment__isnull=False)
        if self.value() == "unpaid":
            return queryset.filter(payment__isnull=True, total_amount__gt=0)
        return queryset.filter(total_amount__exact=0)


class OrderProductFilter(SimpleListFilter):
    title = _("product")
    parameter_name = "product"

    def lookups(self, request, model_admin):
        qs = model_admin.get_queryset(request)
        types = qs.filter(order_items__product__product__isnull=False).values_list(
            "order_items__product__product__id", "order_items__product__product__name"
        )
        return list(types.order_by("order_items__product__product__id").distinct())

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        return queryset.filter(order_items__product__product__id__contains=self.value())


@register(Order)
class OrderAdmin(admin.ModelAdmin):
    class Media:
        pass

    inlines = [
        OrderItemInline,
    ]
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    search_fields = (
        "id",
        "payer__username",
        "payer__first_name",
        "payer__last_name",
        "payer__profile__nickname",
    )

    list_display = (
        "id",
        "shift",
        "created_at",
        "order_description",
        "num_items",
        "discount",
        "_total_amount",
        "paid",
        "payer",
    )
    list_filter = [
        OrderShiftFilter,
        OrderMemberFilter,
        OrderPaymentFilter,
        OrderProductFilter,
    ]

    fields = (
        "id",
        "shift",
        "created_at",
        "created_by",
        "order_description",
        "num_items",
        "age_restricted",
        "subtotal",
        "discount",
        "total_amount",
        "payer",
        "payment",
        "payment_url",
    )

    readonly_fields = (
        "id",
        "created_at",
        "created_by",
        "order_description",
        "num_items",
        "subtotal",
        "total_amount",
        "_total_amount",
        "_is_free",
        "age_restricted",
        "payment_url",
    )

    def get_readonly_fields(self, request: HttpRequest, obj: Order = None):
        """Disallow changing shift when selected."""
        default_fields = self.readonly_fields

        if not (request.member and request.member.has_perm("sales.custom_prices")):
            default_fields += ("discount",)

        if obj and obj.shift:
            default_fields += ("shift",)

        return default_fields

    def save_model(self, request, obj, form, change):
        obj.created_by = request.user
        obj.save()

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        if object_id:
            obj = self.model.objects.get(pk=object_id)
            if obj.age_restricted and obj.payer and not services.is_adult(obj.payer):
                self.message_user(
                    request,
                    _(
                        "The payer for this order is under-age while the order is age restricted!"
                    ),
                    messages.WARNING,
                )
        return super().changeform_view(request, object_id, form_url, extra_context)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        if not request.member:
            queryset = queryset.none()
        elif not request.member.has_perm("sales.override_manager"):
            queryset = queryset.filter(
                shift__managers__in=request.member.get_member_groups()
            )

        queryset = queryset.select_properties(
            "total_amount", "subtotal", "num_items", "age_restricted"
        )
        queryset = queryset.prefetch_related(
            "shift", "shift__event", "shift__product_list"
        )
        queryset = queryset.prefetch_related(
            "order_items", "order_items__product", "order_items__product__product"
        )
        queryset = queryset.prefetch_related("payment")
        queryset = queryset.prefetch_related("payer")
        return queryset

    def has_add_permission(self, request):
        if not request.member:
            return False
        if not request.member.has_perm("sales.override_manager"):
            if not Shift.objects.filter(
                start__lte=timezone.now(),
                locked=False,
                managers__in=request.member.get_member_groups(),
            ).exists():
                return False
        return super().has_view_permission(request)

    def has_view_permission(self, request, obj=None):
        if obj and not is_manager(request.member, obj.shift):
            return False
        return super().has_view_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        if obj and obj.shift.locked:
            return False
        if obj and obj.payment:
            return False

        if obj and not is_manager(request.member, obj.shift):
            return False

        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.shift.locked:
            return False
        if obj and obj.payment:
            return False

        if obj and not is_manager(request.member, obj.shift):
            return False

        return super().has_delete_permission(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        """Override get form to use payment widget."""
        return super().get_form(
            request,
            obj,
            formfield_callback=partial(
                self.formfield_for_dbfield, request=request, obj=obj
            ),
            **kwargs,
        )

    def formfield_for_dbfield(self, db_field, request, obj=None, **kwargs):
        """Use payment widget for payments."""
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == "payment":
            return Field(
                widget=PaymentWidget(obj=obj), initial=field.initial, required=False
            )
        if db_field.name == "shift":
            field.queryset = Shift.objects.filter(locked=False)
            if not request.member:
                field.queryset = field.queryset.none()
            elif not request.member.has_perm("sales.override_manager"):
                field.queryset = field.queryset.filter(
                    managers__in=request.member.get_member_groups()
                ).distinct()
        return field

    def changelist_view(self, request, extra_context=None):
        if not (request.member and request.member.has_perm("sales.override_manager")):
            self.message_user(
                request,
                _("You are only seeing orders that are relevant to you."),
                messages.WARNING,
            )
        return super().changelist_view(request, extra_context)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        if object_id:
            try:
                obj = self.model.objects.get(pk=object_id)
                if (
                    obj.age_restricted
                    and obj.payer
                    and not services.is_adult(obj.payer)
                ):
                    self.message_user(
                        request,
                        _(
                            "The payer for this order is under-age while the order is age restricted!"
                        ),
                        messages.WARNING,
                    )
            except self.model.DoesNotExist:
                pass
        return super().change_view(request, object_id, form_url, extra_context)

    def order_description(self, obj):
        if obj.order_description:
            return obj.order_description
        return "-"

    def num_items(self, obj):
        return obj.num_items

    def subtotal(self, obj):
        if obj.subtotal:
            return f"€{obj.subtotal:.2f}"
        return "-"

    def discount(self, obj):
        if obj.discount:
            return f"€{obj.discount:.2f}"
        return "-"

    def total_amount(self, obj):
        if obj.total_amount:
            return f"€{obj.total_amount:.2f}"
        return "-"

    def paid(self, obj):
        if obj.total_amount is None or obj.total_amount == 0:
            return None
        return obj.payment is not None

    paid.boolean = True

    def age_restricted(self, obj):
        return bool(obj.age_restricted) if obj else None

    age_restricted.boolean = True
