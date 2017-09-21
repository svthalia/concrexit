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
    event = get_object_or_404(Event, pk=event_id)

    return render(request, 'events/admin/details.html', {
        'event': event,
    })


@staff_member_required
@permission_required('events.change_event')
@organiser_only
@require_http_methods(["POST"])
def change_registration(request, event_id, action=None):
    data = {
        'success': True
    }

    try:
        id = request.POST.get("id", -1)
        checked = json.loads(request.POST.get("checked"))
        obj = Registration.objects.get(event=event_id, pk=id)
        if checked is not None:
            if action == 'present':
                obj.present = checked
            elif action == 'paid':
                obj.paid = checked
            obj.save()
    except Registration.DoesNotExist:
        data['success'] = False

    return JsonResponse(data)


@staff_member_required
@permission_required('events.change_event')
@organiser_only
def export(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    extra_fields = event.registrationinformationfield_set.all()
    registrations = event.registration_set.all()

    header_fields = (
        ['name', 'email', 'paid', 'present',
         'status', 'phone number'] +
        [field.name for field in extra_fields] +
        ['date', 'date cancelled'])

    rows = []
    if event.price == 0:
        header_fields.remove('paid')
    for i, registration in enumerate(registrations):
        if registration.member:
            name = registration.member.get_full_name()
        else:
            name = registration.name
        status = pgettext_lazy('registration status', 'registered')
        cancelled = None
        if registration.date_cancelled:

            if registration.is_late_cancellation():
                status = pgettext_lazy('registration status',
                                       'late cancellation')
            else:
                status = pgettext_lazy('registration status', 'cancelled')
            cancelled = timezone.localtime(registration.date_cancelled)

        elif registration.queue_position:
            status = pgettext_lazy('registration status', 'waiting')
        data = {
            'name': name,
            'date': timezone.localtime(registration.date
                                       ).strftime("%Y-%m-%d %H:%m"),
            'present': _('Yes') if registration.present else '',
            'phone number': (registration.member.phone_number
                             if registration.member
                             else ''),
            'email': (registration.member.user.email
                      if registration.member
                      else ''),
            'status': status,
            'date cancelled': cancelled,
        }
        if event.price > 0:
            if registration.payment == 'cash_payment':
                data['paid'] = _('Cash')
            elif registration.payment == 'pin_payment':
                data['paid'] = _('Pin')
            else:
                data['paid'] = _('No')

        data.update({field['field'].name: field['value'] for field in
                     registration.information_fields})
        rows.append(data)

    response = HttpResponse(content_type='text/csv')
    writer = csv.DictWriter(response, header_fields)
    writer.writeheader()

    rows = sorted(rows,
                  key=lambda row:
                  (row['status'] == pgettext_lazy('registration status',
                                                  'late cancellation'),
                   row['date']),
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
    event = get_object_or_404(Event, pk=event_id)
    registrations = event.registration_set.filter(
        date_cancelled=None).prefetch_related('member__user')
    registrations = registrations[:event.max_participants]
    addresses = [r.member.user.email for r in registrations if r.member]
    no_addresses = [r.name for r in registrations if not r.member]
    return render(request, 'events/admin/email_export.html',
                  {'event': event, 'addresses': addresses,
                   'no_addresses': no_addresses})


@staff_member_required
@permission_required('events.change_event')
@organiser_only
def all_present(request, event_id):
    event = get_object_or_404(Event, pk=event_id)

    if event.max_participants is None:
        registrations_query = event.registration_set.filter(
            date_cancelled=None)
    else:
        registrations_query = (event.registration_set
                               .filter(date_cancelled=None)
                               .order_by('date')[:event.max_participants])

    event.registration_set.filter(pk__in=registrations_query).update(
        present=True, payment='cash_payment')

    return HttpResponseRedirect('/events/admin/{}'.format(event_id))
