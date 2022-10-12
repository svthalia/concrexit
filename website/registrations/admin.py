"""Registers admin interfaces for the registrations module."""
from functools import partial

from django.contrib import admin, messages
from django.contrib.admin.utils import model_ngettext
from django.forms import Field
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django_easy_admin_object_actions.admin import ObjectActionsMixin
from django_easy_admin_object_actions.decorators import object_action

from payments.widgets import PaymentWidget
from . import services
from .emails import send_registration_email_confirmation
from .forms import RegistrationAdminForm
from .models import Entry, Registration, Renewal, Reference


class ReferenceInline(admin.StackedInline):
    model = Reference
    extra = 0


def _show_message(model_admin, request, n, message, error):
    """Show a message in the Django Admin."""
    if n == 0:
        model_admin.message_user(request, error, messages.ERROR)
    else:
        model_admin.message_user(
            request,
            message % {"count": n, "items": model_ngettext(model_admin.opts, n)},
            messages.SUCCESS,
        )


@admin.register(Registration)
class RegistrationAdmin(ObjectActionsMixin, admin.ModelAdmin):
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
    actions = ["accept_selected", "reject_selected"]
    form = RegistrationAdminForm

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
            **kwargs
        )

    def formfield_for_dbfield(self, db_field, request, obj=None, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == "payment":
            return Field(
                widget=PaymentWidget(obj=obj), initial=field.initial, required=False
            )
        return field


    def get_readonly_fields(self, request, obj=None):
        if obj is None or obj.status not in (
            Entry.STATUS_REJECTED,
            Entry.STATUS_ACCEPTED,
            Entry.STATUS_COMPLETED,
        ):
            return ["status", "created_at", "updated_at", "payment", "contribution"]
        return [
            field.name
            for field in self.model._meta.get_fields()
            if field.name not in ["payment", "no_references"] and field.editable
        ]

    @staticmethod
    def name(obj):
        return obj.get_full_name()

    def reject_selected(self, request, queryset):
        """Reject the selected entries."""
        if request.user.has_perm("registrations.review_entries"):
            rows_updated = services.reject_entries(request.user.pk, queryset)
            _show_message(
                self,
                request,
                rows_updated,
                message=_("Successfully rejected %(count)d %(items)s."),
                error=_("The selected registration(s) could not be rejected."),
            )

    reject_selected.short_description = _("Reject selected registrations")
    reject_selected.allowed_permissions = ("review",)

    def accept_selected(self, request, queryset):
        """Accept the selected entries."""
        if request.user.has_perm("registrations.review_entries"):
            rows_updated = services.accept_entries(request.user.pk, queryset)
            _show_message(
                self,
                request,
                rows_updated,
                message=_("Successfully accepted %(count)d %(items)s."),
                error=_("The selected registration(s) could not be accepted."),
            )

    accept_selected.short_description = _("Accept selected registrations")
    accept_selected.allowed_permissions = ("review",)

    def has_review_permission(self, request):
        """Check if the user has the review permission."""
        return request.user.has_perm("registrations.review_entries")

    def has_change_permission(self, request, obj=None):
        """Completed registrations are read-only."""
        return (
            False
            if obj and obj.status == Entry.STATUS_COMPLETED
            else super().has_change_permission(request, obj)
        )


    @object_action(
        label=_("Resend email confirmation"),
        parameter_name="_resendemail",
        permissions="registrations.review_entries",
        condition=lambda _, obj: obj.status == Entry.STATUS_CONFIRM,
        log_message=_("Confirmation email resent"),
    )
    def resend_confirmation_email(self, _, obj):
        """Resend the confirmation email."""
        if obj:
            send_registration_email_confirmation(obj)
            self.message_user(
                _, _("Confirmation email successfully resent."), messages.SUCCESS
            )
            return redirect("admin:registrations_registration_change", obj.pk)

    @object_action(
        label=_("Accept"),
        parameter_name="_accept",
        permissions="registrations.review_entries",
        extra_classes="accept",
        condition=lambda _, obj: obj.status == Entry.STATUS_REVIEW,
        log_message=_("Accepted"),
        perform_after_saving=True,
    )
    def accept(self, request, obj):
        """Approve the entry."""
        if obj:
            services.accept_entries(request.user.pk, Entry.objects.filter(pk=obj.pk))
            return redirect("admin:registrations_registration_change", obj.pk)

    @object_action(
        label=_("Reject"),
        parameter_name="_reject",
        permissions="registrations.review_entries",
        extra_classes="reject",
        condition=lambda _, obj: obj.status == Entry.STATUS_REVIEW,
        log_message=_("Rejected"),
        perform_after_saving=True,
    )
    def reject(self, request, obj):
        if obj:
            services.reject_entries(request.user.pk, Entry.objects.filter(pk=obj.pk))
            return redirect("admin:registrations_registration_change", obj.pk)

    @object_action(
        label=_("Revert"),
        parameter_name="_revert",
        permissions="registrations.review_entries",
        condition=lambda _, obj: obj.status in (Entry.STATUS_ACCEPTED, Entry.STATUS_REJECTED),
        log_message=_("Reverted"),
        perform_after_saving=True,
    )
    def revert(self, request, obj):
        """Reverse the review status."""
        if obj:
            services.revert_entry(request.user.pk, obj)
            return redirect("admin:registrations_registration_change", obj.pk)

    object_actions_after_related_objects = ["resend_confirmation_email", "reject", "accept", "revert"]


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
    actions = RegistrationAdmin.actions

    def get_readonly_fields(self, request, obj=None):
        """Make all fields read-only and add member if needed."""
        fields = super().get_readonly_fields(request, obj)
        if obj is None or obj.status not in (
            Entry.STATUS_REJECTED,
            Entry.STATUS_ACCEPTED,
            Entry.STATUS_COMPLETED,
        ):
            fields.remove("contribution")
        if "member" not in fields and obj is not None:
            return fields + ["member"]
        return fields

    @staticmethod
    def name(obj):
        return obj.member.get_full_name()

    name.short_description = _("name")

    @staticmethod
    def email(obj):
        return obj.member.email
