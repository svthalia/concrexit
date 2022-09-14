"""Register admin pages for the models."""
import datetime
from import_export.admin import ExportMixin
from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Count, Q
from django.http import HttpResponse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from members import services
from members.models import EmailChange, Member
from .resources import UserEmailListResource, UserListResource
from . import forms, models


class MembershipInline(admin.StackedInline):
    model = models.Membership
    classes = ["collapse"]
    extra = 0


class ProfileInline(admin.StackedInline):
    fields = [
        "starting_year",
        "programme",
        "address_street",
        "address_street2",
        "address_postal_code",
        "address_city",
        "address_country",
        "student_number",
        "phone_number",
        "receive_optin",
        "receive_newsletter",
        "receive_magazine",
        "birthday",
        "show_birthday",
        "initials",
        "nickname",
        "display_name_preference",
        "profile_description",
        "website",
        "photo",
        "emergency_contact",
        "emergency_contact_phone_number",
        "event_permissions",
    ]
    classes = ["collapse"]
    model = models.Profile
    can_delete = False

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if obj and obj.is_staff:
            fields = fields + ["email_gsuite_only"]
        return fields


class MembershipTypeListFilter(admin.SimpleListFilter):
    title = _("current membership type")
    parameter_name = "membership"

    def lookups(self, request, model_admin):
        return models.Membership.MEMBERSHIP_TYPES + (("none", _("None")),)

    def queryset(self, request, queryset):
        if not self.value():
            return queryset
        if self.value() == "none":
            return queryset.exclude(
                ~Q(membership=None)
                & (
                    Q(membership__until__isnull=True)
                    | Q(membership__until__gt=timezone.now().date())
                )
            )

        return queryset.exclude(membership=None).filter(
            Q(membership__until__isnull=True)
            | Q(membership__until__gt=timezone.now().date()),
            membership__type=self.value(),
        )


class AgeListFilter(admin.SimpleListFilter):
    title = _("Age")
    parameter_name = "birthday"

    def lookups(self, request, model_admin):
        return (
            ("18+", _("≥ 18")),
            ("18-", _("< 18")),
            ("unknown", _("Unknown")),
        )

    def queryset(self, request, queryset):
        if not self.value():
            return queryset

        today = datetime.date.today()
        eighteen_years_ago = today.replace(year=today.year - 18)

        if self.value() == "unknown":
            return queryset.filter(profile__birthday__isnull=True)
        if self.value() == "18+":
            return queryset.filter(profile__birthday__lte=eighteen_years_ago)
        if self.value() == "18-":
            return queryset.filter(profile__birthday__gt=eighteen_years_ago)

        return queryset


class HasPermissionsFilter(admin.SimpleListFilter):
    title = _("Has individual permissions")
    parameter_name = "permissions"

    def lookups(self, request, model_admin):
        return (
            ("yes", _("Yes")),
            ("no", _("No")),
        )

    def queryset(self, request, queryset):
        if not self.value():
            return queryset

        queryset = queryset.annotate(permission_count=Count("user_permissions"))

        if self.value() == "yes":
            return queryset.filter(permission_count__gt=0)

        return queryset.filter(permission_count=0)


class UserAdmin(ExportMixin, BaseUserAdmin):
    resource_classes = (UserEmailListResource, UserListResource)
    form = forms.UserChangeForm
    add_form = forms.UserCreationForm

    actions = [
        "minimise_data",
    ]

    inlines = (
        ProfileInline,
        MembershipInline,
    )
    list_filter = (
        MembershipTypeListFilter,
        "is_superuser",
        HasPermissionsFilter,
        "groups",
        AgeListFilter,
        "profile__event_permissions",
        "profile__receive_optin",
        "profile__receive_newsletter",
        "profile__receive_magazine",
        "profile__starting_year",
    )

    fieldsets = (
        (
            _("Personal"),
            {"fields": ("first_name", "last_name", "email", "username", "password")},
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                    "date_joined",
                    "last_login",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def minimise_data(self, request, queryset):
        processed = len(
            services.execute_data_minimisation(
                members=Member.objects.filter(pk__in=queryset)
            )
        )
        if processed == 0:
            self.message_user(
                request,
                _(
                    "Data minimisation could not be executed "
                    "for the selected user(s)."
                ),
                messages.ERROR,
            )
        else:
            self.message_user(
                request,
                _("Data minimisation was executed for {} user(s).").format(processed),
                messages.SUCCESS,
            )

    minimise_data.short_description = _("Minimise data for the selected users")


@admin.register(models.Member)
class MemberAdmin(UserAdmin):
    def has_module_permission(self, request):
        return False


admin.site.register(EmailChange)

# re-register User admin
admin.site.unregister(get_user_model())
admin.site.register(get_user_model(), UserAdmin)
