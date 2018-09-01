"""Registers admin interfaces for the activemembers module"""
import csv
import datetime

from django import forms
from django.db.models import Q
from django.contrib import admin, messages
from django.contrib.auth.models import Permission
from django.http import HttpResponse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from activemembers import models
from activemembers.forms import MemberGroupMembershipForm
from utils.translation import TranslatedModelAdmin
from utils.snippets import datetime_to_lectureyear


class MemberGroupMembershipInlineFormSet(forms.BaseInlineFormSet):
    """
    Solely here for performance reasons.

    Needed because the `__str__()` of `MemberGroupMembership` (which is displayed
    above each inline form) uses the username, name of the member and name of
    the group.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queryset = self.queryset.select_related(
            'member', 'group').filter(until=None)


class MemberGroupMembershipInline(admin.StackedInline):
    """Inline for group memberships"""
    model = models.MemberGroupMembership
    formset = MemberGroupMembershipInlineFormSet
    can_delete = False
    ordering = ('since',)
    extra = 0
    autocomplete_fields = ('member',)


class CommitteeForm(forms.ModelForm):
    """
    Solely here for performance reasons.

    Needed because the `__str__()` of `Permission` (which is displayed in the
    permissions selection box) also prints the corresponding app and
    `content_type` for each permission.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['permissions'].queryset = (Permission
                                               .objects
                                               .select_related('content_type'))


@admin.register(models.Committee)
class CommitteeAdmin(TranslatedModelAdmin):
    """Manage the committees"""
    inlines = (MemberGroupMembershipInline,)
    form = CommitteeForm
    list_display = ('name', 'since', 'until', 'active', 'email')
    list_filter = ('until', 'active',)
    search_fields = ('name', 'description')
    filter_horizontal = ('permissions',)

    fields = ('name', 'description', 'photo', 'permissions', 'since',
              'until', 'contact_mailinglist', 'contact_email',
              'wiki_namespace', 'active')

    def email(self, instance):
        if instance.contact_email:
            return instance.contact_email
        elif instance.contact_mailinglist:
            return instance.contact_mailinglist.name + '@thalia.nu'
        return None

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.exclude(board=None)


@admin.register(models.Board)
class BoardAdmin(TranslatedModelAdmin):
    """Manage the board"""
    inlines = (MemberGroupMembershipInline,)
    form = CommitteeForm
    exclude = ('is_board',)
    filter_horizontal = ('permissions',)

    fields = ('name', 'description', 'photo', 'permissions',
              'contact_mailinglist', 'contact_email', 'since', 'until',)


class BoardFilter(admin.SimpleListFilter):
    """Filter memberships on board-only"""
    title = _('board memberships')
    parameter_name = 'board'

    def lookups(self, request, model_admin):
        return [
            ('only', _('Only board memberships')),
            ('none', _('No board memberships')),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'only':
            return queryset.exclude(group__board=None)
        elif self.value() == 'none':
            return queryset.filter(group__board=None)

        return queryset


class LectureYearFilter(admin.SimpleListFilter):
    """Filter the memberships on those started or ended in a lecture year"""
    title = _('lecture year')
    parameter_name = 'lecture_year'

    def lookups(self, request, model_admin):
        current_year = datetime_to_lectureyear(timezone.now())
        first_year = datetime_to_lectureyear(
                models.MemberGroupMembership.objects.earliest('since').since
        )

        return [(year, '{}-{}'.format(year, year+1))
                for year in range(first_year, current_year+1)]

    def queryset(self, request, queryset):
        if not self.value():
            return queryset

        year = int(self.value())
        first_of_september = datetime.date(year=year, month=9, day=1)

        return queryset.exclude(until__lt=first_of_september)


class ActiveMembershipsFilter(admin.SimpleListFilter):
    """Filter the memberships by whether they are active or not"""
    title = _('active memberships')
    parameter_name = 'active'

    def lookups(self, request, model_name):
        return (
            ('active', _('Active')),
            ('inactive', _('Inactive')),
        )

    def queryset(self, request, queryset):
        now = timezone.now()

        if self.value() == 'active':
            return queryset.filter(Q(until__isnull=True) |
                                   Q(until__gte=now))

        if self.value() == 'inactive':
            return queryset.filter(until__lt=now)


@admin.register(models.MemberGroupMembership)
class MemberGroupMembershipAdmin(TranslatedModelAdmin):
    """Manage the group memberships"""
    form = MemberGroupMembershipForm
    list_display = ('member', 'group', 'since', 'until', 'chair', 'role')
    list_filter = ('group', BoardFilter, LectureYearFilter,
                   ActiveMembershipsFilter)
    list_select_related = ('member', 'group',)
    search_fields = ('member__first_name', 'member__last_name',
                     'member__email')

    actions = ('export',)

    def changelist_view(self, request, extra_context=None):
        self.message_user(request, _('Do not edit existing memberships if the '
                                     'chair of a group has changed, add a '
                                     'new membership instead.'),
                          messages.WARNING)
        return super().changelist_view(request, extra_context)

    def export(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = ('attachment;'
                                           'filename='
                                           '"group_memberships.csv"')
        writer = csv.writer(response)
        writer.writerow([
            _('First name'),
            _('Last name'),
            _('Email'),
            _('Group'),
            _('Member since'),
            _('Member until'),
            _('Chair of the group'),
            _('Role'),
        ])

        for membership in queryset:
            writer.writerow([
                membership.member.first_name,
                membership.member.last_name,
                membership.member.email,
                membership.group,
                membership.since,
                membership.until,
                membership.chair,
                membership.role,
            ])

        return response
    export.short_description = _('Export selected memberships')


@admin.register(models.Mentorship)
class MentorshipAdmin(admin.ModelAdmin):
    """Manage the mentorships"""
    list_select_related = ('member',)
