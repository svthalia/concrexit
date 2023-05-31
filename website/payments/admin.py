"""Registers admin interfaces for the payments module."""
from collections import OrderedDict

from django.contrib import admin, messages
from django.contrib.admin import ModelAdmin
from django.contrib.admin.utils import model_ngettext
from django.db.models import QuerySet
from django.db.models.query_utils import Q
from django.http import HttpRequest, HttpResponse
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from import_export.admin import ExportActionMixin

from payments import admin_views, services
from payments.forms import BankAccountAdminForm, BatchPaymentInlineAdminForm

from .models import BankAccount, Batch, Payment, PaymentUser
from .resources import BankAccountResource, PaymentResource


def _show_message(
    model_admin: ModelAdmin, request: HttpRequest, n: int, message: str, error: str
) -> None:
    if n == 0:
        model_admin.message_user(request, error, messages.ERROR)
    else:
        model_admin.message_user(
            request,
            message % {"count": n, "items": model_ngettext(model_admin.opts, n)},
            messages.SUCCESS,
        )


@admin.register(Payment)
class PaymentAdmin(ExportActionMixin, admin.ModelAdmin):
    """Manage the payments."""

    resource_classes = (PaymentResource,)
    list_display = (
        "created_at",
        "amount",
        "type",
        "paid_by_link",
        "processed_by_link",
        "batch_link",
        "topic",
    )
    list_filter = ("type", "batch")
    list_select_related = ("paid_by", "processed_by", "batch")
    date_hierarchy = "created_at"
    fields = (
        "created_at",
        "amount",
        "type",
        "paid_by",
        "processed_by",
        "topic",
        "notes",
        "batch",
    )
    readonly_fields = (
        "created_at",
        "amount",
        "paid_by",
        "processed_by",
        "type",
        "topic",
        "notes",
        "batch",
    )
    search_fields = (
        "topic",
        "notes",
        "paid_by__username",
        "paid_by__first_name",
        "paid_by__last_name",
        "processed_by__username",
        "processed_by__first_name",
        "processed_by__last_name",
        "amount",
    )
    ordering = ("-created_at",)
    autocomplete_fields = ("paid_by", "processed_by")
    actions = [
        "add_to_new_batch",
        "add_to_last_batch",
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

    def paid_by_link(self, obj: Payment) -> str:
        return self._member_link(obj.paid_by)

    paid_by_link.admin_order_field = "paid_by"
    paid_by_link.short_description = _("paid by")

    @staticmethod
    def _batch_link(payment: Payment, batch: Batch) -> str:
        if batch:
            return format_html(
                "<a href='{}'>{}</a>", batch.get_absolute_url(), str(batch)
            )
        if payment.type == Payment.TPAY:
            return _("No batch attached")
        return ""

    def batch_link(self, obj: Payment) -> str:
        return self._batch_link(obj, obj.batch)

    batch_link.admin_order_field = "batch"
    batch_link.short_description = _("in batch")

    def processed_by_link(self, obj: Payment) -> str:
        return self._member_link(obj.processed_by)

    processed_by_link.admin_order_field = "processed_by"
    processed_by_link.short_description = _("processed by")

    def has_delete_permission(self, request, obj=None):
        if isinstance(obj, Payment):
            if obj.batch and obj.batch.processed:
                return False
        if (
            "payment/" in request.path
            and request.POST
            and request.POST.get("action") == "delete_selected"
        ):
            for payment_id in request.POST.getlist("_selected_action"):
                payment = Payment.objects.get(id=payment_id)
                if payment.batch and payment.batch.processed:
                    return False

        return super().has_delete_permission(request, obj)

    def get_field_queryset(self, db, db_field, request):
        if str(db_field) == "payments.Payment.batch":
            return Batch.objects.filter(processed=False)
        return super().get_field_queryset(db, db_field, request)

    def get_readonly_fields(self, request: HttpRequest, obj: Payment = None):
        if not obj:
            return "created_at", "processed_by", "batch"
        if obj.type == Payment.TPAY and not (obj.batch and obj.batch.processed):
            return (
                "created_at",
                "amount",
                "type",
                "paid_by",
                "processed_by",
                "notes",
                "topic",
            )
        return super().get_readonly_fields(request, obj)

    def get_actions(self, request: HttpRequest) -> OrderedDict:
        """Get the actions for the payments.

        Hide the processing actions if the right permissions are missing
        """
        actions = super().get_actions(request)
        if not request.user.has_perm("payments.process_batches"):
            del actions["add_to_new_batch"]
            del actions["add_to_last_batch"]

        return actions

    def add_to_new_batch(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Add selected TPAY payments to a new batch."""
        tpays = queryset.filter(type=Payment.TPAY)
        if len(tpays) > 0:
            batch = Batch.objects.create()
            tpays.update(batch=batch)
        _show_message(
            self,
            request,
            len(tpays),
            _("Successfully added {} payments to new batch").format(len(tpays)),
            _("No payments using Thalia Pay are selected, no batch is created"),
        )

    add_to_new_batch.short_description = _(
        "Add selected Thalia Pay payments to a new batch"
    )

    def add_to_last_batch(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Add selected TPAY payments to the last batch."""
        tpays = queryset.filter(type=Payment.TPAY)
        if len(tpays) > 0:
            batch = Batch.objects.last()
            if batch is None:
                self.message_user(request, _("No batches available."), messages.ERROR)
            elif not batch.processed:
                batch.save()
                tpays.update(batch=batch)
                self.message_user(
                    request,
                    _("Successfully added {} payments to {}").format(len(tpays), batch),
                    messages.SUCCESS,
                )
            else:
                self.message_user(
                    request,
                    _("The last batch {} is already processed").format(batch),
                    messages.ERROR,
                )
        else:
            self.message_user(
                request,
                _("No payments using Thalia Pay are selected, no batch is created"),
                messages.ERROR,
            )

    add_to_last_batch.short_description = _(
        "Add selected Thalia Pay payments to the last batch"
    )

    def get_urls(self) -> list:
        urls = super().get_urls()
        custom_urls = [
            path(
                "<str:app_label>/<str:model_name>/<payable>/create/",
                self.admin_site.admin_view(admin_views.PaymentAdminView.as_view()),
                name="payments_payment_create",
            ),
        ]
        return custom_urls + urls


class ValidAccountFilter(admin.SimpleListFilter):
    """Filter the memberships by whether they are active or not."""

    title = _("mandates")
    parameter_name = "active"

    def lookups(self, request, model_admin) -> tuple:
        return (
            ("valid", _("Valid")),
            ("invalid", _("Invalid")),
            ("none", _("None")),
        )

    def queryset(self, request, queryset) -> QuerySet:
        now = timezone.now()

        if self.value() == "valid":
            return queryset.filter(
                Q(valid_from__lte=now) & Q(valid_until=None) | Q(valid_until__lt=now)
            )

        if self.value() == "invalid":
            return queryset.filter(valid_until__gte=now)

        if self.value() == "none":
            return queryset.filter(valid_from=None)

        return queryset


class PaymentsInline(admin.TabularInline):
    """The inline for payments in the Batch admin."""

    model = Payment
    readonly_fields = (
        "topic",
        "paid_by",
        "amount",
        "created_at",
        "notes",
    )
    form = BatchPaymentInlineAdminForm
    extra = 0
    max_num = 0
    can_delete = False

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if obj and obj.processed:
            fields.remove("remove_batch")
        return fields


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    """Manage payment batches."""

    inlines = (PaymentsInline,)
    list_display = (
        "id",
        "description",
        "withdrawal_date",
        "start_date",
        "end_date",
        "total_amount",
        "payments_count",
        "processing_date",
        "processed",
    )
    fields = (
        "id",
        "description",
        "withdrawal_date",
        "processed",
        "processing_date",
        "total_amount",
    )
    search_fields = (
        "id",
        "description",
        "withdrawal_date",
    )

    def get_readonly_fields(self, request: HttpRequest, obj: Batch = None):
        default_fields = (
            "id",
            "processed",
            "processing_date",
            "total_amount",
        )
        if obj and obj.processed:
            return (
                "description",
                "withdrawal_date",
            ) + default_fields
        return default_fields

    def has_delete_permission(self, request, obj=None):
        if isinstance(obj, Batch):
            if obj.processed:
                return False
        if (
            "batch/" in request.path
            and request.POST
            and request.POST.get("action") == "delete_selected"
        ):
            for payment_id in request.POST.getlist("_selected_action"):
                if Batch.objects.get(id=payment_id).processed:
                    return False

        return super().has_delete_permission(request, obj)

    def get_urls(self) -> list:
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:pk>/process/",
                self.admin_site.admin_view(admin_views.BatchProcessAdminView.as_view()),
                name="payments_batch_process",
            ),
            path(
                "<int:pk>/export/",
                self.admin_site.admin_view(admin_views.BatchExportAdminView.as_view()),
                name="payments_batch_export",
            ),
            path(
                "<int:pk>/export-topic/",
                self.admin_site.admin_view(
                    admin_views.BatchTopicExportAdminView.as_view()
                ),
                name="payments_batch_export_topic",
            ),
            path(
                "<int:pk>/topic-description/",
                self.admin_site.admin_view(
                    admin_views.BatchTopicDescriptionAdminView.as_view()
                ),
                name="payments_batch_topic_description",
            ),
            path(
                "new_filled/",
                self.admin_site.admin_view(
                    admin_views.BatchNewFilledAdminView.as_view()
                ),
                name="payments_batch_new_batch_filled",
            ),
        ]
        return custom_urls + urls

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)

        for instance in instances:
            if instance.batch and not instance.batch.processed:
                instance.batch = None
            instance.save()
        formset.save_m2m()

    def changeform_view(
        self,
        request: HttpRequest,
        object_id: str = None,
        form_url: str = "",
        extra_context: dict = None,
    ) -> HttpResponse:
        """Render the change formview.

        Only allow when the batch has not been processed yet.
        """
        extra_context = extra_context or {}
        obj = None
        if object_id is not None and request.user.has_perm("payments.process_batches"):
            obj = Batch.objects.get(id=object_id)

        extra_context["batch"] = obj
        return super().changeform_view(request, object_id, form_url, extra_context)


@admin.register(BankAccount)
class BankAccountAdmin(ExportActionMixin, admin.ModelAdmin):
    """Manage bank accounts."""

    resource_classes = (BankAccountResource,)
    list_display = ("iban", "owner_link", "last_used", "valid_from", "valid_until")
    fields = (
        "created_at",
        "last_used",
        "owner",
        "iban",
        "bic",
        "initials",
        "last_name",
        "mandate_no",
        "valid_from",
        "valid_until",
        "signature",
        "can_be_revoked",
    )
    readonly_fields = (
        "created_at",
        "can_be_revoked",
    )
    search_fields = ("owner__username", "owner__first_name", "owner__last_name", "iban")
    autocomplete_fields = ("owner",)
    actions = ["set_last_used"]
    form = BankAccountAdminForm

    def owner_link(self, obj: BankAccount) -> str:
        if obj.owner:
            return format_html(
                "<a href='{}'>{}</a>",
                reverse("admin:auth_user_change", args=[obj.owner.pk]),
                obj.owner.get_full_name(),
            )
        return ""

    owner_link.admin_order_field = "owner"
    owner_link.short_description = _("owner")

    def can_be_revoked(self, obj: BankAccount):
        return obj.can_be_revoked

    can_be_revoked.boolean = True

    def set_last_used(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Set the last used date of selected accounts."""
        if request.user.has_perm("payments.change_bankaccount"):
            updated = services.update_last_used(queryset)
            _show_message(
                self,
                request,
                updated,
                message=_("Successfully updated %(count)d %(items)s."),
                error=_("The selected account(s) could not be updated."),
            )

    set_last_used.short_description = _("Update the last used date")


class BankAccountInline(admin.TabularInline):
    model = BankAccount
    fields = (
        "iban",
        "bic",
        "mandate_no",
        "valid_from",
        "valid_until",
        "last_used",
    )
    show_change_link = True

    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class PaymentInline(admin.TabularInline):
    model = Payment
    fk_name = "paid_by"
    fields = (
        "created_at",
        "type",
        "amount",
        "topic",
        "notes",
        "batch",
    )
    ordering = ("-created_at",)

    show_change_link = True

    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ThaliaPayAllowedFilter(admin.SimpleListFilter):
    title = _("Thalia Pay allowed")
    parameter_name = "tpay_allowed"

    def lookups(self, request, model_admin):
        return ("1", _("Yes")), ("0", _("No"))

    def queryset(self, request, queryset):
        if self.value() == "1":
            return queryset.filter(tpay_allowed=True)
        if self.value() == "0":
            return queryset.exclude(tpay_allowed=True)
        return queryset


class ThaliaPayEnabledFilter(admin.SimpleListFilter):
    title = _("Thalia Pay enabled")
    parameter_name = "tpay_enabled"

    def lookups(self, request, model_admin):
        return ("1", _("Yes")), ("0", _("No"))

    def queryset(self, request, queryset):
        if self.value() == "1":
            return queryset.filter(tpay_enabled=True)
        if self.value() == "0":
            return queryset.exclude(tpay_enabled=True)
        return queryset


class ThaliaPayBalanceFilter(admin.SimpleListFilter):
    title = _("Thalia Pay balance")
    parameter_name = "tpay_balance"

    def lookups(self, request, model_admin):
        return (
            ("0", "€0,00"),
            ("1", ">€0.00"),
        )

    def queryset(self, request, queryset):
        if self.value() == "0":
            return queryset.filter(tpay_balance=0)
        if self.value() == "1":
            return queryset.exclude(tpay_balance=0)
        return queryset


@admin.register(PaymentUser)
class PaymentUserAdmin(admin.ModelAdmin):
    list_display = (
        "__str__",
        "email",
        "get_tpay_allowed",
        "get_tpay_enabled",
        "get_tpay_balance",
    )
    list_filter = [
        ThaliaPayAllowedFilter,
        ThaliaPayEnabledFilter,
        ThaliaPayBalanceFilter,
    ]

    inlines = [BankAccountInline, PaymentInline]

    fields = (
        "user_link",
        "get_tpay_allowed",
        "get_tpay_enabled",
        "get_tpay_balance",
    )

    readonly_fields = (
        "user_link",
        "get_tpay_allowed",
        "get_tpay_enabled",
        "get_tpay_balance",
    )

    search_fields = (
        "first_name",
        "last_name",
        "username",
        "email",
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.prefetch_related("bank_accounts", "paid_payment_set")
        queryset = queryset.select_properties(
            "tpay_balance",
            "tpay_enabled",
            "tpay_allowed",
        )
        return queryset

    def get_tpay_balance(self, obj):
        return f"€ {obj.tpay_balance:.2f}" if obj.tpay_enabled else "-"

    get_tpay_balance.short_description = _("balance")

    def get_tpay_enabled(self, obj):
        return obj.tpay_enabled

    get_tpay_enabled.short_description = _("Thalia Pay enabled")
    get_tpay_enabled.boolean = True

    def get_tpay_allowed(self, obj):
        return obj.tpay_allowed

    get_tpay_allowed.short_description = _("Thalia Pay allowed")
    get_tpay_allowed.boolean = True

    def user_link(self, obj):
        return (
            format_html(
                "<a href='{}'>{}</a>",
                reverse("admin:auth_user_change", args=[obj.pk]),
                obj.get_full_name(),
            )
            if obj
            else ""
        )

    user_link.admin_order_field = "user"
    user_link.short_description = _("user")

    actions = ["disallow_thalia_pay", "allow_thalia_pay"]

    def disallow_thalia_pay(self, request, queryset):
        count = 0
        for x in queryset:
            changed = x.disallow_tpay()
            count += 1 if changed else 0
        messages.success(
            request,
            _(f"Succesfully disallowed Thalia Pay for {count} users."),
        )

    disallow_thalia_pay.short_description = _("Disallow Thalia Pay for selected users")

    def allow_thalia_pay(self, request, queryset):
        count = 0
        for x in queryset:
            changed = x.allow_tpay()
            count += 1 if changed else 0
        messages.success(
            request,
            _(f"Succesfully allowed Thalia Pay for {count} users."),
        )

    allow_thalia_pay.short_description = _("Allow Thalia Pay for selected users")

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
