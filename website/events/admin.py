# -*- coding: utf-8 -*-
from django import forms
from django.urls import reverse
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.utils.http import is_safe_url
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from utils.translation import TranslatedModelAdmin
from activemembers.models import Committee
from members.models import Member
from . import models


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


class RegistrationInformationFieldForm(forms.ModelForm):

    order = forms.IntegerField(label=_('order'), initial=0)

    class Meta:
        fields = '__all__'
        model = models.RegistrationInformationField


class RegistrationInformationFieldInline(admin.StackedInline):
    form = RegistrationInformationFieldForm
    extra = 0
    model = models.RegistrationInformationField
    ordering = ('_order',)

    radio_fields = {'type': admin.VERTICAL}


@admin.register(models.Event)
class EventAdmin(DoNextModelAdmin):
    inlines = (RegistrationInformationFieldInline,)
    fields = ('title', 'description', 'start', 'end', 'organiser',
              'registration_start', 'registration_end', 'cancel_deadline',
              'location', 'map_location', 'price', 'cost',
              'max_participants', 'no_registration_message', 'published')
    list_display = ('overview_link', 'start', 'registration_start',
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

    def edit_link(self, obj):
        return _('Edit')
    edit_link.short_description = ''

    def num_participants(self, obj):
        """Pretty-print the number of participants"""
        num = (obj.registration_set
               .filter(date_cancelled__lt=timezone.now()).count())
        if not obj.max_participants:
            return '{}/∞'.format(num)
        return '{}/{}'.format(num, obj.max_participants)
    num_participants.short_description = _('Number of participants')

    def make_published(self, request, queryset):
        queryset.update(published=True)
    make_published.short_description = _('Publish selected events')

    def make_unpublished(self, request, queryset):
        queryset.update(published=False)
    make_unpublished.short_description = _('Unpublish selected events')

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
            try:
                if not request.user.is_superuser:
                    member = request.user.member
                    kwargs['queryset'] = Committee.active_committees.filter(
                        members=member)
            except Member.DoesNotExist:
                pass
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


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
