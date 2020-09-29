"""Registers admin interfaces for the payments module"""
import csv
from collections import OrderedDict

from django.contrib import admin, messages
from django.contrib.admin import ModelAdmin
from django.contrib.admin.utils import model_ngettext
from django.db.models import QuerySet
from django.db.models.query_utils import Q
from django.http import HttpResponse, HttpRequest
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _

from members.models import Member
from payments import services, admin_views
from payments.forms import BankAccountAdminForm, BatchPaymentInlineAdminForm
from .models import Payment, BankAccount, Batch


def _show_message(
    admin: ModelAdmin, request: HttpRequest, n: int, message: str, error: str
) -> None:
    if n == 0:
        admin.message_user(request, error, messages.ERROR)
    else:
        admin.message_user(
            request,
            message % {"count": n, "items": model_ngettext(admin.opts, n)},
            messages.SUCCESS,
        )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Manage the payments"""

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
        "export_csv",
    ]

    @staticmethod
    def _member_link(member: Member) -> str:
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
        elif payment.type == Payment.TPAY:
            return _("No batch attached")
        else:
            return ""

    def batch_link(self, obj: Payment) -> str:
        return self._batch_link(obj, obj.batch)

    batch_link.admin_order_field = "in batch"
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
            for id in request.POST.getlist("_selected_action"):
                payment = Payment.objects.get(id=id)
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
        """Get the actions for the payments"""
        """Hide the processing actions if the right permissions are missing"""
        actions = super().get_actions(request)
        if not request.user.has_perm("payments.process_batches"):
            del actions["add_to_new_batch"]
            del actions["add_to_last_batch"]

        return actions

    def add_to_new_batch(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Add selected TPAY payments to a new batch"""
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
        """Add selected TPAY payments to the last batch"""
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
                _(
                    f"No payments using Thalia Pay are selected, "
                    f"no batch is created"
                ),
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

    def export_csv(self, request: HttpRequest, queryset: QuerySet) -> HttpResponse:
        """
        Export a CSV of payments
        :param request: Request
        :param queryset: Items to be exported
        """
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment;filename="payments.csv"'
        writer = csv.writer(response)
        headers = [
            _("created"),
            _("amount"),
            _("type"),
            _("processor"),
            _("payer id"),
            _("payer name"),
            _("notes"),
        ]
        writer.writerow([capfirst(x) for x in headers])
        for payment in queryset:
            writer.writerow(
                [
                    payment.created_at,
                    payment.amount,
                    payment.get_type_display(),
                    payment.processed_by.get_full_name()
                    if payment.processed_by
                    else "-",
                    payment.paid_by.pk if payment.paid_by else "-",
                    payment.paid_by.get_full_name() if payment.paid_by else "-",
                    payment.notes,
                ]
            )
        return response

    export_csv.short_description = _("Export")


class ValidAccountFilter(admin.SimpleListFilter):
    """Filter the memberships by whether they are active or not"""

    title = _("mandates")
    parameter_name = "active"

    def lookups(self, request, model_name) -> tuple:
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
    """The inline for payments in the Batch admin"""

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
    """Manage payment batches"""

    inlines = (PaymentsInline,)
    list_display = (
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
        "description",
        "withdrawal_date",
        "processed",
        "processing_date",
        "total_amount",
    )
    search_fields = (
        "description",
        "withdrawal_date",
    )

    def get_readonly_fields(self, request: HttpRequest, obj: Batch = None):
        default_fields = (
            "processed",
            "processing_date",
            "total_amount",
        )
        if obj and obj.processed:
            return ("description", "withdrawal_date",) + default_fields
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
            for id in request.POST.getlist("_selected_action"):
                if Batch.objects.get(id=id).processed:
                    return False

        return super().has_delete_permission(request, obj)

    def get_urls(self) -> list:
        urls = super().get_urls()
        custom_urls = [
            path(
                "<uuid:pk>/process/",
                self.admin_site.admin_view(admin_views.BatchProcessAdminView.as_view()),
                name="payments_batch_process",
            ),
            path(
                "<uuid:pk>/export/",
                self.admin_site.admin_view(admin_views.BatchExportAdminView.as_view()),
                name="payments_batch_export",
            ),
            path(
                "<uuid:pk>/export-topic/",
                self.admin_site.admin_view(
                    admin_views.BatchTopicExportAdminView.as_view()
                ),
                name="payments_batch_export_topic",
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
        """
        Renders the change formview
        Only allow when the batch has not been processed yet
        """
        extra_context = extra_context or {}
        obj = None
        if object_id is not None and request.user.has_perm("payments.process_batches"):
            obj = Batch.objects.get(id=object_id)

        extra_context["batch"] = obj
        return super().changeform_view(request, object_id, form_url, extra_context)


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    """Manage bank accounts"""

    list_display = ("iban", "owner_link", "last_used", "valid_from", "valid_until")
    list_filter = (ValidAccountFilter, "owner__profile__auto_renew")
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

    def set_last_used(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Set the last used date of selected accounts"""
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

    def export_csv(self, request: HttpRequest, queryset: QuerySet) -> HttpResponse:
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment;filename="accounts.csv"'
        writer = csv.writer(response)
        headers = [
            _("created"),
            _("name"),
            _("reference"),
            _("IBAN"),
            _("BIC"),
            _("valid from"),
            _("valid until"),
            _("signature"),
        ]
        writer.writerow([capfirst(x) for x in headers])
        for account in queryset:
            writer.writerow(
                [
                    account.created_at,
                    account.name,
                    account.mandate_no,
                    account.iban,
                    account.bic or "",
                    account.valid_from or "",
                    account.valid_until or "",
                    account.signature or "",
                ]
            )
        return response

    export_csv.short_description = _("Export")
