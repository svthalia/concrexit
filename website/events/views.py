import csv
import json
from datetime import timedelta

from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required, login_required
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _, pgettext_lazy

from .models import Event, Registration, RegistrationInformationField
from .forms import FieldsForm


@staff_member_required
@permission_required('events.change_event')
def admin_details(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    n = event.max_participants
    registrations = list(event.registration_set.filter(date_cancelled=None))
    cancellations = event.registration_set.exclude(date_cancelled=None)
    return render(request, 'events/admin/details.html', {
        'event': event,
        'registrations': registrations[:n],
        'waiting': registrations[n:] if n else [],
        'cancellations': cancellations,
    })


@staff_member_required
@permission_required('events.change_event')
@require_http_methods(["POST"])
def admin_change_registration(request, event_id, action=None):
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
def export(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    extra_fields = event.registrationinformationfield_set.all()
    registrations = event.registration_set.all()

    header_fields = (
        ['name', 'paid', 'present', 'email',
         'phone number'] +
        [field.name for field in extra_fields] +
        ['status', 'date', 'date cancelled'])

    rows = []
    capacity = event.max_participants
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
            if capacity is not None:
                capacity += 1
            status = pgettext_lazy('registration status', 'cancelled')
            cancelled = timezone.localtime(registration.date_cancelled)
        elif capacity and i >= capacity:
            status = pgettext_lazy('registration status', 'waiting')
        data = {
            'name': name,
            'date': timezone.localtime(registration.date
                                       ).strftime("%Y-%m-%d %H:%m"),
            'dateobj': registration.date,
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
            data['paid'] = _('Yes') if registration.paid else ''

        data.update({field['field'].name: field['value'] for field in
                     registration.registration_information()})
        rows.append(data)

    response = HttpResponse(content_type='text/csv')
    writer = csv.DictWriter(response, header_fields)
    writer.writeheader()

    def order(item):
        if item['status'] == 'cancelled':
            return item['dateobj'] + timedelta(days=10000)
        elif item['status'] == 'registered':
            return item['dateobj'] - timedelta(days=10000)
        else:
            return item['dateobj']

    for row in sorted(rows, key=order):
        r = row.copy()
        del r['dateobj']
        writer.writerow(r)

    response['Content-Disposition'] = (
        'attachment; filename="{}.csv"'.format(slugify(event.title)))
    return response


def index(request):
    upcoming_activity = Event.objects.filter(
        published=True,
        end__gte=timezone.now()
    ).order_by('end').first()

    return render(request, 'events/index.html', {
        'upcoming_activity': upcoming_activity
    })


def event(request, event_id):
    event = get_object_or_404(
        Event.objects.filter(published=True),
        pk=event_id
    )
    registrations = event.registration_set.filter(
        date_cancelled=None)[:event.max_participants]

    context = {
        'event': event,
        'registrations': registrations,
        'user': request.user,
    }

    if event.max_participants:
        perc = 100.0 * len(registrations) / event.max_participants
        context['registration_percentage'] = perc

    try:
        registration = Registration.objects.get(
            event=event,
            member=request.user.member
        )
        context['registration'] = registration
    except Registration.DoesNotExist:
        pass

    return render(request, 'events/event.html', context)


@login_required
def registration(request, event_id, action=None):
    event = get_object_or_404(
        Event.objects.filter(published=True),
        pk=event_id
    )

    if (event.status != Event.REGISTRATION_NOT_NEEDED and
            request.user.member.current_membership is not None):
        try:
            obj = Registration.objects.get(
                event=event,
                member=request.user.member
            )
        except Registration.DoesNotExist:
            obj = None

        success_message = None
        error_message = None
        show_fields = False
        if action == 'register' and (
            event.status == Event.REGISTRATION_OPEN or
            event.status == Event.REGISTRATION_OPEN_NO_CANCEL
        ):
            if event.has_fields():
                show_fields = True

            if obj is None:
                obj = Registration()
                obj.event = event
                obj.member = request.user.member
            elif obj.date_cancelled is not None:
                if obj.is_late_cancellation():
                    error_message = _("You cannot re-register anymore since "
                                      "you've cancelled after the deadline.")
                else:
                    obj.date = timezone.now()
                    obj.date_cancelled = None
            else:
                error_message = _("You were already registered.")

            if error_message is None:
                success_message = _("Registration successful.")
        elif (action == 'update' and
              event.has_fields() and
              obj is not None and
              (event.status == Event.REGISTRATION_OPEN or
               event.status == Event.REGISTRATION_OPEN_NO_CANCEL)):
            show_fields = True
            success_message = _("Registration successfully updated.")
        elif action == 'cancel':
            if (obj is not None and
                    obj.date_cancelled is None):
                # Note that this doesn't remove the values for the
                # information fields that the user entered upon registering.
                # But this is regarded as a feature, not a bug. Especially
                # since the values will still appear in the backend.
                obj.date_cancelled = timezone.now()
                success_message = _("Registration successfully cancelled.")
            else:
                error_message = _("You were not registered for this event.")

        if show_fields:
            if request.POST:
                form = FieldsForm(request.POST, registration=obj)
                if form.is_valid():
                    obj.save()
                    form_field_values = form.field_values()
                    for field in form_field_values:
                        if (field['field'].type ==
                                RegistrationInformationField.INTEGER_FIELD
                                and field['value'] is None):
                            field['value'] = 0
                        field['field'].set_value_for(obj,
                                                     field['value'])
            else:
                form = FieldsForm(registration=obj)
                context = {'event': event, 'form': form, 'action': action}
                return render(request, 'events/event_fields.html', context)

        if success_message is not None:
            messages.success(request, success_message)
        elif error_message is not None:
            messages.error(request, error_message)
        obj.save()

    return redirect(event)
