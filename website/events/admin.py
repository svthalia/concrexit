# -*- coding: utf-8 -*-
"""Registers admin interfaces for the events module"""
from django.contrib import admin
from django.core.exceptions import DisallowedRedirect
from django.db.models import Max, Min
from django.http import HttpResponseRedirect
from django.template.defaultfilters import date as _date
from django.urls import reverse
from django.utils import timezone
from django.utils.datetime_safe import date
from django.utils.html import format_html
from django.utils.http import is_safe_url
from django.utils.translation import ugettext_lazy as _

from activemembers.models import MemberGroup
from events import services
from members.models import Member
from pizzas.models import PizzaEvent
from utils.snippets import datetime_to_lectureyear
from utils.translation import TranslatedModelAdmin
from . import forms, models


def _do_next(request, response):
    """See DoNextModelAdmin"""
    if 'next' in request.GET:
        if not is_safe_url(request.GET['next'],
                           allowed_hosts={request.get_host()}):
            raise DisallowedRedirect
        elif '_save' in request.POST:
            return HttpResponseRedirect(request.GET['next'])
        elif response is not None:
            return HttpResponseRedirect('{}?{}'.format(
                response.url, request.GET.urlencode()))
    return response


class DoNextModelAdmin(TranslatedModelAdmin):
    """
    This class adds processing of a `next` parameter in the urls
    of the add and change admin forms. If it is set and safe this
    override will redirect the user to the provided url.
    """

    def response_add(self, request, obj):
        res = super().response_add(request, obj)
        return _do_next(request, res)

    def response_change(self, request, obj):
        res = super().response_change(request, obj)
        return _do_next(request, res)


class RegistrationInformationFieldInline(admin.StackedInline):
    """The inline for registration information fields in the Event admin"""
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


class PizzaEventInline(admin.StackedInline):
    """The inline for pizza events in the Event admin"""
    model = PizzaEvent
    extra = 0
    max_num = 1


class LectureYearFilter(admin.SimpleListFilter):
    """Filter the events on those started or ended in a lecture year"""
    title = _('lecture year')
    parameter_name = 'lecture_year'

    def lookups(self, request, model_admin):
        objects_end = models.Event.objects.aggregate(Max('end'))
        objects_start = models.Event.objects.aggregate(Min('start'))

        if objects_end['end__max'] and objects_start['start__min']:
            year_end = datetime_to_lectureyear(objects_end['end__max'])
            year_start = datetime_to_lectureyear(objects_start['start__min'])

            return [(year, '{}-{}'.format(year, year+1))
                    for year in range(year_end, year_start-1, -1)]
        return []

    def queryset(self, request, queryset):
        if not self.value():
            return queryset

        year = int(self.value())
        year_start = date(year=year, month=9, day=1)
        year_end = date(year=year + 1, month=9, day=1)

        return queryset.filter(start__gte=year_start, end__lte=year_end)


@admin.register(models.Event)
class EventAdmin(DoNextModelAdmin):
    """Manage the events"""
    inlines = (RegistrationInformationFieldInline, PizzaEventInline,)
    fields = ('title', 'description', 'start', 'end', 'organiser', 'category',
              'registration_start', 'registration_end', 'cancel_deadline',
              'send_cancel_email', 'location', 'map_location', 'price', 'fine',
              'max_participants', 'no_registration_message', 'published')
    list_display = ('overview_link', 'event_date', 'registration_date',
                    'num_participants', 'organiser', 'category', 'published',
                    'edit_link')
    list_display_links = ('edit_link',)
    list_filter = (LectureYearFilter, 'start', 'published', 'category')
    actions = ('make_published', 'make_unpublished')
    date_hierarchy = 'start'
    search_fields = ('title', 'description')

    def overview_link(self, obj):
        return format_html('<a href="{link}">{title}</a>',
                           link=reverse('events:admin-details',
                                        kwargs={'event_id': obj.pk}),
                           title=obj.title)

    def has_change_permission(self, request, event=None):
        """Only allow access to the change form if the user is an organiser"""
        if (event is not None and
                not services.is_organiser(request.member, event)):
            return False
        return super().has_change_permission(request, event)

    def event_date(self, obj):
        event_date = timezone.make_naive(obj.start)
        return _date(event_date, "l d b Y, G:i")
    event_date.short_description = _('Event Date')
    event_date.admin_order_field = 'start'

    def registration_date(self, obj):
        if obj.registration_start is not None:
            start_date = timezone.make_naive(obj.registration_start)
        else:
            start_date = obj.registration_start

        return _date(start_date, "l d b Y, G:i")
    registration_date.short_description = _('Registration Start')
    registration_date.admin_order_field = 'registration_start'

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
        """Action to change the status of the event"""
        self._change_published(request, queryset, True)
    make_published.short_description = _('Publish selected events')

    def make_unpublished(self, request, queryset):
        """Action to change the status of the event"""
        self._change_published(request, queryset, False)
    make_unpublished.short_description = _('Unpublish selected events')

    @staticmethod
    def _change_published(request, queryset, published):
        if not request.user.is_superuser:
            queryset = queryset.filter(
                organiser__in=request.member.get_member_groups())
        queryset.update(published=published)

    def save_formset(self, request, form, formset, change):
        """Save formsets with their order"""
        formset.save()

        informationfield_forms = (
            x for x in formset.forms if
            isinstance(x, forms.RegistrationInformationFieldForm)
        )
        form.instance.set_registrationinformationfield_order([
            f.instance.pk
            for f in sorted(informationfield_forms,
                            key=lambda x: (x.cleaned_data['order'],
                                           x.instance.pk))
        ])
        form.instance.save()

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        """Customise formfield for organiser"""
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == 'organiser':
            # Disable add/change/delete buttons
            field.widget.can_add_related = False
            field.widget.can_change_related = False
            field.widget.can_delete_related = False
        return field

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Customise the organiser formfield, limit the options"""
        if db_field.name == 'organiser':
            # Use custom queryset for organiser field
            # Only get the current active committees the user is a member of
            if not (request.user.is_superuser or
                    request.user.has_perm('events.override_organiser')):
                kwargs['queryset'] = request.member.get_member_groups()
            else:
                # Hide old boards and inactive committees for new events
                if 'add' in request.path:
                    kwargs['queryset'] = (
                        MemberGroup.active_objects.all() |
                        MemberGroup.objects
                        .filter(board=None)
                        .exclude(until__lt=(timezone.now() -
                                 timezone.timedelta(weeks=1)))
                    )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_actions(self, request):
        actions = super(EventAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions

    def get_prepopulated_fields(self, request, obj):
        # FIXME(Django bug) move this back to a normal ``prepopulated_fields``
        # class field when bug https://code.djangoproject.com/ticket/29929 gets
        # fixed
        if self.has_change_permission(request, obj):
            return {'map_location': (f'location_en',)}
        return super().get_prepopulated_fields(request, obj)

    def get_formsets_with_inlines(self, request, obj=None):
        for inline in self.get_inline_instances(request, obj):
            if self.has_change_permission(request, obj) or obj is None:
                yield inline.get_formset(request, obj), inline


@admin.register(models.Registration)
class RegistrationAdmin(DoNextModelAdmin):
    """Custom admin for registrations"""

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        """Customise the formfields of event and member"""
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name in ('event', 'member'):
            # Disable add/change/delete buttons
            field.widget.can_add_related = False
            field.widget.can_change_related = False
            field.widget.can_delete_related = False
        return field

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Customise the formfields of event and member"""
        if db_field.name == 'event':
            # allow to restrict event
            if request.GET.get('event_pk'):
                kwargs['queryset'] = models.Event.objects.filter(
                    pk=int(request.GET['event_pk']))
        elif db_field.name == 'member':
            # Filter the queryset to current members only
            kwargs['queryset'] = Member.current_members.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
