import csv
import json

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_http_methods

from events.decorators import organiser_only
from .models import Event, Registration


@staff_member_required
@permission_required('events.change_event')
@organiser_only
def details(request, event_id):
    """
    Renders an overview of registration for the specified event

    :param request: the request object
    :param event_id: the primary key of the event
    :return: HttpResponse 200 with the page HTML
    """
    event = get_object_or_404(Event, pk=event_id)

    return render(request, 'events/admin/details.html', {
        'event': event,
    })


@staff_member_required
@permission_required('events.change_event')
@organiser_only
@require_http_methods(["POST"])
def change_registration(request, event_id, action=None):
    """
    JSON call to change the status of a registration

    :param request: the request object
    :param event_id: the primary key of the event
    :param action: specifies what should be changed
    :return: JsonResponse with a success status
    """
    data = {
        'success': True
    }

    try:
        id = request.POST.get("id", -1)
        obj = Registration.objects.get(event=event_id, pk=id)
        if action == 'present':
            checked = json.loads(request.POST.get("checked"))
            if checked is not None:
                obj.present = checked
                obj.save()
        elif action == 'payment':
            value = request.POST.get("value")
            if value is not None:
                obj.payment = value
                obj.save()
    except Registration.DoesNotExist:
        data['success'] = False

    return JsonResponse(data)


@staff_member_required
@permission_required('events.change_event')
def export(request, event_id):
    """
    Export the registration of a specified event

    :param request: the request object
    :param event_id: the primary key of the event
    :return: A CSV containing all registrations for the event
    """
    event = get_object_or_404(Event, pk=event_id)
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


@staff_member_required
@permission_required('events.change_event')
def export_email(request, event_id):
    """
    Renders a page that outputs all email addresses of registered members
    for an event

    :param request: the request object
    :param event_id: the primary key of the event
    :return: HttpResponse 200 with the HTML of the page
    """
    event = get_object_or_404(Event, pk=event_id)
    registrations = event.registration_set.filter(
        date_cancelled=None)
    registrations = registrations[:event.max_participants]
    addresses = [r.member.email for r in registrations if r.member]
    no_addresses = [r.name for r in registrations if not r.member]
    return render(request, 'events/admin/email_export.html',
                  {'event': event, 'addresses': addresses,
                   'no_addresses': no_addresses})


@staff_member_required
@permission_required('events.change_event')
@organiser_only
def all_present(request, event_id):
    """
    Mark all registrations of an event as present

    :param request: the request object
    :param event_id: the primary key of the event
    :return: HttpResponse 302 to the event admin page
    """
    event = get_object_or_404(Event, pk=event_id)

    if event.max_participants is None:
        registrations_query = event.registration_set.filter(
            date_cancelled=None)
    else:
        registrations_query = (event.registration_set
                               .filter(date_cancelled=None)
                               .order_by('date')[:event.max_participants])

    event.registration_set.filter(pk__in=registrations_query).update(
        present=True, payment=Registration.PAYMENT_CASH)

    return HttpResponseRedirect('/events/admin/{}'.format(event_id))
