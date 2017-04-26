# -*- coding: utf-8 -*-
from django.contrib import admin
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.http import is_safe_url
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import date as _date

from members.models import Member
from utils.translation import TranslatedModelAdmin
from . import forms, models


def _do_next(request, response):
    if 'next' in request.GET and is_safe_url(request.GET['next']):
        return HttpResponseRedirect(request.GET['next'])
    else:
        return response


class DoNextModelAdmin(TranslatedModelAdmin):

    def response_add(self, request, obj):
        res = super().response_add(request, obj)
        return _do_next(request, res)

    def response_change(self, request, obj):
        res = super().response_change(request, obj)
        return _do_next(request, res)


class RegistrationInformationFieldInline(admin.StackedInline):
    form = forms.RegistrationInformationFieldForm
    extra = 0
    model = models.RegistrationInformationField
    ordering = ('_order',)

    radio_fields = {'type': admin.VERTICAL}

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        if obj is not None:
            count = obj.registrationinformationfield_set.count()
            formset.form.declared_fields['order'].initial = count
        return formset


@admin.register(models.Event)
class EventAdmin(DoNextModelAdmin):
    inlines = (RegistrationInformationFieldInline,)
    fields = ('title', 'description', 'start', 'end', 'organiser',
              'registration_start', 'registration_end', 'cancel_deadline',
              'location', 'map_location', 'price', 'fine',
              'max_participants', 'no_registration_message', 'published')
    list_display = ('overview_link', 'event_date', 'registration_date',
                    'num_participants', 'organiser', 'published', 'edit_link')
    list_display_links = ('edit_link',)
    list_filter = ('start', 'published')
    actions = ('make_published', 'make_unpublished')
    date_hierarchy = 'start'
    search_fields = ('title', 'description')
    prepopulated_fields = {'map_location': ('location',)}

    def overview_link(self, obj):
        return format_html('<a href="{link}">{title}</a>',
                           link=reverse('events:admin-details',
                                        kwargs={'event_id': obj.pk}),
                           title=obj.title)

    def has_change_permission(self, request, event=None):
        try:
            if (not request.user.is_superuser and event is not None and
                    not request.user.has_perm('events.override_organiser')):
                committees = request.user.member.get_committees().filter(
                    Q(pk=event.organiser.pk)).count()
                if committees == 0:
                    return False
        except Member.DoesNotExist:
            pass
        return super().has_change_permission(request, event)

    def event_date(self, obj):
        event_date = obj.start
        return _date(event_date, "l d b Y, G:i")
    event_date.short_description = _('Event Date')

    def registration_date(self, obj):
        start_date = obj.registration_start
        return _date(start_date, "l d b Y, G:i")
    registration_date.short_description = _('Registration Start')

    def edit_link(self, obj):
        return _('Edit')
    edit_link.short_description = ''

    def num_participants(self, obj):
        """Pretty-print the number of participants"""
        num = (obj.registration_set
               .exclude(date_cancelled__lt=timezone.now()).count())
        if not obj.max_participants:
            return '{}/∞'.format(num)
        return '{}/{}'.format(num, obj.max_participants)
    num_participants.short_description = _('Number of participants')

    def make_published(self, request, queryset):
        self._change_published(request, queryset, True)
    make_published.short_description = _('Publish selected events')

    def make_unpublished(self, request, queryset):
        self._change_published(request, queryset, False)
    make_unpublished.short_description = _('Unpublish selected events')

    @staticmethod
    def _change_published(request, queryset, published):
        try:
            if not request.user.is_superuser:
                queryset = queryset.filter(
                    organiser__in=request.user.member.get_committees())
            queryset.update(published=published)
        except Member.DoesNotExist:
            pass

    def save_formset(self, request, form, formset, change):
        """Save formsets with their order"""
        formset.save()

        form.instance.set_registrationinformationfield_order([
            f.instance.pk
            for f in sorted(formset.forms,
                            key=lambda x: (x.cleaned_data['order'],
                                           x.instance.pk))
        ])
        form.instance.save()

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == 'organiser':
            # Disable add/change/delete buttons
            field.widget.can_add_related = False
            field.widget.can_change_related = False
            field.widget.can_delete_related = False
        return field

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'organiser':
            # Use custom queryset for organiser field
            # Only get the current active committees the user is a member of
            try:
                if not request.user.is_superuser:
                    kwargs['queryset'] = request.user.member.get_committees()

            except Member.DoesNotExist:
                pass
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_actions(self, request):
        actions = super(EventAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions


@admin.register(models.Registration)
class RegistrationAdmin(DoNextModelAdmin):
    """Custom admin for registrations"""

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name in ('event', 'member'):
            # Disable add/change/delete buttons
            field.widget.can_add_related = False
            field.widget.can_change_related = False
            field.widget.can_delete_related = False
        return field

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'event':
            # allow to restrict event
            if request.GET.get('event_pk'):
                kwargs['queryset'] = models.Event.objects.filter(
                    pk=int(request.GET['event_pk']))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
