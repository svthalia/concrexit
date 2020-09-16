"""
This module registers admin pages for the models
"""
import csv
import datetime
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.db.models import Q, Count
from django.http import HttpResponse
from django.urls import path
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from members import services, admin_views
from members.models import EmailChange, Member
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
        "auto_renew",
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
        eightteen_years_ago = today.replace(year=today.year - 18)

        if self.value() == "unknown":
            return queryset.filter(profile__birthday__isnull=True)
        elif self.value() == "18+":
            return queryset.filter(profile__birthday__lte=eightteen_years_ago)
        elif self.value() == "18-":
            return queryset.filter(profile__birthday__gt=eightteen_years_ago)

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


class UserAdmin(BaseUserAdmin):
    change_list_template = "admin/members/change_list.html"
    form = forms.UserChangeForm
    add_form = forms.UserCreationForm

    actions = [
        "address_csv_export",
        "student_number_csv_export",
        "email_csv_export",
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
        "profile__auto_renew",
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

    def email_csv_export(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response[
            "Content-Disposition"
        ] = 'attachment;\
                                           filename="email.csv"'
        writer = csv.writer(response)
        writer.writerow([_("First name"), _("Last name"), _("Email")])
        for user in queryset:
            writer.writerow(
                [user.first_name, user.last_name, user.email,]
            )
        return response

    email_csv_export.short_description = _(
        "Download email addresses for selected users"
    )

    def address_csv_export(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response[
            "Content-Disposition"
        ] = 'attachment;\
                                           filename="addresses.csv"'
        writer = csv.writer(response)
        writer.writerow(
            [
                _("First name"),
                _("Last name"),
                _("Address"),
                _("Address line 2"),
                _("Postal code"),
                _("City"),
                _("Country"),
            ]
        )
        for user in queryset.exclude(profile=None):
            writer.writerow(
                [
                    user.first_name,
                    user.last_name,
                    user.profile.address_street,
                    user.profile.address_street2,
                    user.profile.address_postal_code,
                    user.profile.address_city,
                    user.profile.get_address_country_display(),
                ]
            )
        return response

    address_csv_export.short_description = _("Download addresses for selected users")

    def student_number_csv_export(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment;filename="student_numbers.csv"'
        writer = csv.writer(response)
        writer.writerow([_("First name"), _("Last name"), _("Student number")])
        for user in queryset.exclude(profile=None):
            writer.writerow(
                [user.first_name, user.last_name, user.profile.student_number]
            )
        return response

    student_number_csv_export.short_description = _(
        "Download student number export for selected users"
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

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "iban-export/",
                self.admin_site.admin_view(admin_views.IbanExportView.as_view()),
                name="members_member_ibanexport",
            ),
        ]
        return custom_urls + urls


@admin.register(models.Member)
class MemberAdmin(UserAdmin):
    def has_module_permission(self, reuqest):
        return False


admin.site.register(EmailChange)

# re-register User admin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
