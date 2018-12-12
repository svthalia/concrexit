import csv

from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.text import slugify
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from django.views import View
from django.views.generic import DetailView, TemplateView

from events.decorators import organiser_only
from .models import Event, Registration


@method_decorator([staff_member_required, ], name='dispatch')
@method_decorator(organiser_only, name='dispatch')
class EventAdminDetails(DetailView):
    """
    Renders an overview of registrations for the specified event
    """
    template_name = 'events/admin/details.html'
    model = Event
    context_object_name = 'event'


@method_decorator([staff_member_required, ], name='dispatch')
@method_decorator(organiser_only, name='dispatch')
class EventRegistrationsExport(View):
    """
    View to export registrations
    """
    template_name = 'events/admin/details.html'

    def get(self, request, pk):
        """
        Export the registration of a specified event

        :param request: the request object
        :param pk: the primary key of the event
        :return: A CSV containing all registrations for the event
        """
        event = get_object_or_404(Event, pk=pk)
        extra_fields = event.registrationinformationfield_set.all()
        registrations = event.registration_set.all()

        header_fields = (
            [_('Name'), _('Email'), _('Paid'), _('Present'),
             _('Status'), _('Phone number')] +
            [field.name for field in extra_fields] +
            [_('Date'), _('Date cancelled')])

        rows = []
        if event.price == 0:
            header_fields.remove(_('Paid'))
        for i, registration in enumerate(registrations):
            if registration.member:
                name = registration.member.get_full_name()
            else:
                name = registration.name
            status = pgettext_lazy('registration status',
                                   'registered').capitalize()
            cancelled = None
            if registration.date_cancelled:

                if registration.is_late_cancellation():
                    status = pgettext_lazy('registration status',
                                           'late cancellation').capitalize()
                else:
                    status = pgettext_lazy('registration status',
                                           'cancelled').capitalize()
                cancelled = timezone.localtime(registration.date_cancelled)

            elif registration.queue_position:
                status = pgettext_lazy('registration status', 'waiting')
            data = {
                _('Name'): name,
                _('Date'): timezone.localtime(registration.date),
                _('Present'): _('Yes') if registration.present else '',
                _('Phone number'): (registration.member.profile.phone_number
                                    if registration.member
                                    else ''),
                _('Email'): (registration.member.email
                             if registration.member
                             else ''),
                _('Status'): status,
                _('Date cancelled'): cancelled,
            }
            if event.price > 0:
                if registration.payment == registration.PAYMENT_CASH:
                    data[_('Paid')] = _('Cash')
                elif registration.payment == registration.PAYMENT_CARD:
                    data[_('Paid')] = _('Pin')
                else:
                    data[_('Paid')] = _('No')

            data.update({field['field'].name: field['value'] for field in
                         registration.information_fields})
            rows.append(data)

        response = HttpResponse(content_type='text/csv')
        writer = csv.DictWriter(response, header_fields)
        writer.writeheader()

        rows = sorted(rows,
                      key=lambda row:
                      (row[_('Status')] == pgettext_lazy(
                          'registration status',
                          'late cancellation').capitalize(),
                       row[_('Date')]),
                      reverse=True,
                      )

        for row in rows:
            writer.writerow(row)

        response['Content-Disposition'] = (
            'attachment; filename="{}.csv"'.format(slugify(event.title)))
        return response


@method_decorator([staff_member_required, ], name='dispatch')
@method_decorator(organiser_only, name='dispatch')
class EventRegistrationEmailsExport(TemplateView):
    """
    Renders a page that outputs all email addresses of registered members
    for an event
    """
    template_name = 'events/admin/email_export.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = get_object_or_404(Event, pk=kwargs['pk'])
        registrations = event.registration_set.filter(
            date_cancelled=None)
        registrations = registrations[:event.max_participants]
        addresses = [r.member.email for r in registrations if r.member]
        no_addresses = [r.name for r in registrations if not r.member]
        context['event'] = event
        context['addresses'] = addresses
        context['no_addresses'] = no_addresses
        return context


@method_decorator([staff_member_required, ], name='dispatch')
@method_decorator(organiser_only, name='dispatch')
class EventRegistrationsMarkPresent(View):
    """
    Renders a page that outputs all email addresses of registered members
    for an event
    """
    template_name = 'events/admin/email_export.html'

    def get(self, request, pk):
        """
        Mark all registrations of an event as present

        :param request: the request object
        :param pk: the primary key of the event
        :return: HttpResponse 302 to the event admin page
        """
        event = get_object_or_404(Event, pk=pk)

        if event.max_participants is None:
            registrations_query = event.registration_set.filter(
                date_cancelled=None)
        else:
            registrations_query = (event.registration_set
                                   .filter(date_cancelled=None)
                                   .order_by('date')[:event.max_participants])

        event.registration_set.filter(pk__in=registrations_query).update(
            present=True, payment=Registration.PAYMENT_CASH)

        return HttpResponseRedirect(reverse('admin:events_event_details',
                                            args=[str(event.pk)]))
