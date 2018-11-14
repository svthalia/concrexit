"""
This module registers admin pages for the models
"""
import csv
import datetime
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from members.models import EmailChange
from . import forms, models


class MembershipInline(admin.StackedInline):
    model = models.Membership
    extra = 0


class ProfileInline(admin.StackedInline):
    fields = ('starting_year', 'programme', 'address_street',
              'address_street2', 'address_postal_code', 'address_city',
              'student_number', 'phone_number', 'receive_optin',
              'receive_newsletter', 'birthday', 'show_birthday',
              'direct_debit_authorized', 'bank_account', 'initials',
              'nickname', 'display_name_preference', 'profile_description',
              'website', 'photo', 'emergency_contact',
              'emergency_contact_phone_number', 'language',
              'event_permissions')
    model = models.Profile
    form = forms.ProfileForm
    can_delete = False


class MembershipTypeListFilter(admin.SimpleListFilter):
    title = _('current membership type')
    parameter_name = 'membership'

    def lookups(self, request, model_admin):
        return models.Membership.MEMBERSHIP_TYPES + (('none', _('None')),)

    def queryset(self, request, queryset):
        if not self.value():
            return queryset
        if self.value() == 'none':
            return queryset.exclude(
                ~Q(membership=None) & (
                    Q(membership__until__isnull=True) |
                    Q(membership__until__gt=timezone.now().date())
                ))

        return (queryset
                .exclude(membership=None)
                .filter(Q(membership__until__isnull=True) |
                        Q(membership__until__gt=timezone.now().date()),
                        membership__type=self.value()))


class AgeListFilter(admin.SimpleListFilter):
    title = _('Age')
    parameter_name = 'birthday'

    def lookups(self, request, model_admin):
        return (
            ('18+', _('≥ 18')),
            ('18-', _('< 18')),
            ('unknown', _('Unknown')),
        )

    def queryset(self, request, queryset):
        if not self.value():
            return queryset

        today = datetime.date.today()
        eightteen_years_ago = today.replace(year=today.year - 18)

        if self.value() == 'unknown':
            return queryset.filter(profile__birthday__isnull=True)
        elif self.value() == '18+':
            return queryset.filter(profile__birthday__lte=eightteen_years_ago)
        elif self.value() == '18-':
            return queryset.filter(profile__birthday__gt=eightteen_years_ago)

        return queryset


class UserAdmin(BaseUserAdmin):
    change_list_template = 'admin/members/change_list.html'
    form = forms.UserChangeForm
    add_form = forms.UserCreationForm

    actions = ['address_csv_export', 'student_number_csv_export']

    inlines = (ProfileInline, MembershipInline,)
    list_filter = (MembershipTypeListFilter,
                   'is_superuser',
                   AgeListFilter,
                   'profile__event_permissions',
                   'profile__starting_year')

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name', 'username', 'email',
                       'send_welcome_email')
        }),
    )

    def address_csv_export(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment;\
                                           filename="addresses.csv"'
        writer = csv.writer(response)
        writer.writerow([_('First name'), _('Last name'), _('Address'),
                         _('Address line 2'), _('Postal code'), _('City')])
        for user in queryset.exclude(profile=None):
            writer.writerow([user.first_name,
                             user.last_name,
                             user.profile.address_street,
                             user.profile.address_street2,
                             user.profile.address_postal_code,
                             user.profile.address_city,
                             ])
        return response
    address_csv_export.short_description = _('Download address label for '
                                             'selected users')

    def student_number_csv_export(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment;\
                                           filename="student_numbers.csv"'
        writer = csv.writer(response)
        writer.writerow([_('First name'), _('Last name'), _('Student number')])
        for user in queryset.exclude(profile=None):
            writer.writerow([user.first_name,
                             user.last_name,
                             user.profile.student_number
                             ])
        return response
    student_number_csv_export.short_description = _('Download student number '
                                                    'label for selected users')


@admin.register(models.Member)
class MemberAdmin(UserAdmin):
    def has_module_permission(self, reuqest):
        return False


admin.site.register(EmailChange)

# re-register User admin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
