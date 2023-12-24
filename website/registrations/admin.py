"""Registers admin interfaces for the registrations module."""
from functools import partial

from django.contrib import admin
from django.forms import Field
from django.utils.translation import gettext_lazy as _

from payments.widgets import PaymentWidget
from registrations.services import (
    accept_registration,
    accept_renewal,
    reject_registration,
    reject_renewal,
)

from .forms import RegistrationAdminForm
from .models import Entry, Reference, Registration, Renewal


class ReferenceInline(admin.StackedInline):
    model = Reference
    extra = 0


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    """Manage the registrations."""

    list_display = (
        "name",
        "email",
        "status",
        "membership_type",
        "contribution",
        "created_at",
        "payment",
        "no_references",
        "reference_count",
    )
    list_filter = (
        "status",
        "programme",
        "membership_type",
        "no_references",
        "payment__type",
        "contribution",
    )
    inlines = (ReferenceInline,)
    search_fields = (
        "first_name",
        "last_name",
        "email",
        "phone_number",
        "student_number",
    )
    date_hierarchy = "created_at"
    fieldsets = (
        (
            _("Application information"),
            {
                "fields": (
                    "created_at",
                    "updated_at",
                    "username",
                    "length",
                    "contribution",
                    "membership_type",
                    "status",
                    "payment",
                    "remarks",
                )
            },
        ),
        (
            _("Personal information"),
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "birthday",
                    "optin_birthday",
                    "email",
                    "optin_mailinglist",
                    "phone_number",
                )
            },
        ),
        (
            _("Address"),
            {
                "fields": (
                    "address_street",
                    "address_street2",
                    "address_postal_code",
                    "address_city",
                    "address_country",
                )
            },
        ),
        (
            _("Financial"),
            {
                "fields": (
                    "direct_debit",
                    "initials",
                    "iban",
                    "bic",
                    "signature",
                )
            },
        ),
        (
            _("University information"),
            {
                "fields": (
                    "student_number",
                    "programme",
                    "starting_year",
                )
            },
        ),
    )

    form = RegistrationAdminForm

    actions = ["accept_registrations", "reject_registrations"]

    def get_actions(self, request):
        actions = super().get_actions(request)

        if not request.user.has_perm("registrations.review_entries"):
            if "accept_registrations" in actions:
                del actions["accept_registrations"]
            if "reject_registrations" in actions:
                del actions["reject_registrations"]

        return actions

    @admin.action(description="Accept selected registrations")
    def accept_registrations(self, request, queryset):  # pragma: no cover
        if queryset.exclude(status=Registration.STATUS_REVIEW).exists():
            self.message_user(
                request, "Only registrations in review can be accepted", "error"
            )
            return

        count = 0
        for registration in queryset:
            try:
                accept_registration(registration, actor=request.user)
                count += 1
            except ValueError as e:
                self.message_user(
                    request, f"Error accepting {registration}: {e.message}", "error"
                )

        self.message_user(request, f"Accepted {count} registrations", "success")

    @admin.action(description="Reject selected registrations")
    def reject_registrations(self, request, queryset):  # pragma: no cover
        if queryset.exclude(status=Registration.STATUS_REVIEW).exists():
            self.message_user(
                request, "Only registrations in review can be rejected", "error"
            )
            return

        count = queryset.count()
        for registration in queryset:
            reject_registration(registration, actor=request.user)

        self.message_user(request, f"Rejected {count} registrations", "success")

    def reference_count(self, obj):
        return obj.reference_set.count()

    reference_count.short_description = _("references")

    def get_form(self, request, obj=None, **kwargs):
        return super().get_form(
            request,
            obj,
            formfield_callback=partial(
                self.formfield_for_dbfield, request=request, obj=obj
            ),
            **kwargs,
        )

    def formfield_for_dbfield(self, db_field, request, obj=None, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == "payment":
            return Field(
                widget=PaymentWidget(obj=obj), initial=field.initial, required=False
            )
        return field

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        """Render the change formview.

        Only allow when the entry has not been processed yet
        """
        obj = None
        can_review = False
        can_resend = False
        can_revert = False
        if object_id is not None and request.user.has_perm(
            "registrations.review_entries"
        ):  # pragma: no cover
            obj = self.get_object(request, object_id)
            if obj is None:
                return self._get_obj_does_not_exist_redirect(
                    request, self.opts, object_id
                )
            can_review = obj.status == Entry.STATUS_REVIEW
            can_revert = obj.status in [Entry.STATUS_ACCEPTED, Entry.STATUS_REJECTED]
            can_resend = obj.status == Entry.STATUS_CONFIRM and isinstance(
                obj, Registration
            )

        return super().changeform_view(
            request,
            object_id,
            form_url,
            {
                "entry": obj,
                "can_review": can_review,
                "can_resend": can_resend,
                "can_revert": can_revert,
            },
        )

    def get_readonly_fields(self, request, obj=None):
        if obj is None or obj.status not in (
            Entry.STATUS_REJECTED,
            Entry.STATUS_ACCEPTED,
            Entry.STATUS_COMPLETED,
        ):
            return ["status", "created_at", "updated_at", "payment"]
        return [
            field.name
            for field in self.model._meta.get_fields()
            if field.name not in ["payment", "no_references"] and field.editable
        ]

    @staticmethod
    def name(obj):
        return obj.get_full_name()

    def has_change_permission(self, request, obj=None):
        """Completed registrations are read-only."""
        return (
            False
            if obj and obj.status == Entry.STATUS_COMPLETED
            else super().has_change_permission(request, obj)
        )

    def has_add_permission(self, request):
        return False

    def save_model(self, request, obj, form, change):
        if obj.status not in (
            Entry.STATUS_REJECTED,
            Entry.STATUS_ACCEPTED,
            Entry.STATUS_COMPLETED,
        ):
            super().save_model(request, obj, form, change)


@admin.register(Renewal)
class RenewalAdmin(RegistrationAdmin):
    """Manage the renewals."""

    list_display = (
        "name",
        "email",
        "status",
        "membership_type",
        "contribution",
        "created_at",
        "payment",
        "no_references",
        "reference_count",
    )
    list_filter = (
        "status",
        "membership_type",
        "no_references",
        "payment__type",
        "contribution",
    )
    search_fields = (
        "member__first_name",
        "member__last_name",
        "member__email",
        "member__profile__phone_number",
        "member__profile__student_number",
    )
    date_hierarchy = "created_at"
    fieldsets = (
        (
            _("Application information"),
            {
                "fields": (
                    "created_at",
                    "updated_at",
                    "length",
                    "contribution",
                    "membership_type",
                    "status",
                    "payment",
                    "remarks",
                    "member",
                )
            },
        ),
    )

    actions = ["accept_renewals", "reject_renewals"]

    def get_actions(self, request):
        actions = super().get_actions(request)

        if not request.user.has_perm("registrations.review_entries"):
            if "accept_renewals" in actions:  # pragma: no cover
                del actions["accept_renewals"]
            if "reject_renewals" in actions:  # pragma: no cover
                del actions["reject_renewals"]

        return actions

    @admin.action(description="Accept selected renewals")
    def accept_renewals(self, request, queryset):  # pragma: no cover
        if queryset.exclude(status=Renewal.STATUS_REVIEW).exists():
            self.message_user(
                request, "Only renewals in review can be accepted", "error"
            )
            return

        count = queryset.count()
        for renewal in queryset:
            accept_renewal(renewal, actor=request.user)
            count += 1

        self.message_user(request, f"Accepted {count} renewals", "success")

    @admin.action(description="Reject selected renewals")
    def reject_renewals(self, request, queryset):  # pragma: no cover
        if queryset.exclude(status=Renewal.STATUS_REVIEW).exists():
            self.message_user(
                request, "Only renewals in review can be rejected", "error"
            )
            return

        count = queryset.count()
        for renewal in queryset:
            reject_renewal(renewal, actor=request.user)

        self.message_user(request, f"Rejected {count} renewals", "success")

    def get_readonly_fields(self, request, obj=None):
        """Make all fields read-only and add member if needed."""
        fields = super().get_readonly_fields(request, obj)
        if "member" not in fields and obj is not None:
            return fields + ["member"]
        return fields

    def has_add_permission(self, request):
        return False

    @staticmethod
    def name(obj):
        return obj.member.get_full_name()

    name.short_description = _("name")

    @staticmethod
    def email(obj):
        return obj.member.email
