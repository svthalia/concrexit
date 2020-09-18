"""Registers admin interfaces for the registrations module"""
from functools import partial

from django.contrib import admin, messages
from django.contrib.admin.utils import model_ngettext
from django.forms import Field
from django.utils.translation import gettext_lazy as _

from payments.widgets import PaymentWidget
from . import services
from .models import Entry, Registration, Renewal, Reference


class ReferenceInline(admin.StackedInline):
    model = Reference
    extra = 0


def _show_message(admin, request, n, message, error):
    """Show a message in the Django Admin"""
    if n == 0:
        admin.message_user(request, error, messages.ERROR)
    else:
        admin.message_user(
            request,
            message % {"count": n, "items": model_ngettext(admin.opts, n)},
            messages.SUCCESS,
        )


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    """Manage the registrations"""

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
                    "mandate",
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
            _("University information"),
            {"fields": ("student_number", "programme", "starting_year",)},
        ),
    )
    actions = ["accept_selected", "reject_selected"]

    def reference_count(self, obj):
        return obj.reference_set.count()

    reference_count.short_description = _("references")

    def get_form(self, request, obj=None, **kwargs):
        kwargs["formfield_callback"] = partial(
            self.formfield_for_dbfield, request=request, obj=obj
        )
        return super().get_form(request, obj, **kwargs)

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        obj = kwargs.pop("obj", None)
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == "payment":
            return Field(
                widget=PaymentWidget(obj=obj), initial=field.initial, required=False
            )
        return field

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        """
        Renders the change formview
        Only allow when the entry has not been processed yet
        """
        obj = None
        can_review = False
        can_resend = False
        can_revert = False
        if object_id is not None and request.user.has_perm(
            "registrations.review_entries"
        ):
            obj = Entry.objects.get(id=object_id)
            can_review = obj.status == Entry.STATUS_REVIEW
            can_revert = obj.status in [Entry.STATUS_ACCEPTED, Entry.STATUS_REJECTED]
            try:
                can_resend = obj.registration.status == Entry.STATUS_CONFIRM
            except Registration.DoesNotExist:
                pass
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
        if obj is None or not (
            obj.status == Entry.STATUS_REJECTED
            or obj.status == Entry.STATUS_ACCEPTED
            or obj.status == Entry.STATUS_COMPLETED
        ):
            return ["status", "created_at", "updated_at"]
        else:
            return [
                field.name
                for field in self.model._meta.get_fields()
                if not field.name in ["payment", "no_references"] and field.editable
            ]

    @staticmethod
    def name(obj):
        return obj.get_full_name()

    def reject_selected(self, request, queryset):
        """Reject the selected entries"""
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
        """Accept the selected entries"""
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
        """Does the user have the review permission?"""
        return request.user.has_perm("registrations.review_entries")

    def save_model(self, request, obj, form, change):
        if not (
            obj.status == Entry.STATUS_REJECTED
            or obj.status == Entry.STATUS_ACCEPTED
            or obj.status == Entry.STATUS_COMPLETED
        ):
            super().save_model(request, obj, form, change)


@admin.register(Renewal)
class RenewalAdmin(RegistrationAdmin):
    """Manage the renewals"""

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
        """Make all fields read-only and add member if needed"""
        fields = super().get_readonly_fields(request, obj)
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
