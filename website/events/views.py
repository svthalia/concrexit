import csv
import json

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMessage
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import get_template
from django.utils import timezone, translation
from django.utils.text import slugify
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_http_methods

from .forms import FieldsForm
from .models import Event, Registration, RegistrationInformationField


@staff_member_required
@permission_required('events.change_event')
def admin_details(request, event_id):
    event = get_object_or_404(Event, pk=event_id)

    if not request.user.is_superuser and event.organiser is not None:
        committees = request.user.member.get_committees().filter(
            pk=event.organiser.pk).count()

        if committees == 0:
            raise PermissionDenied

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

        elif registration.queue_position():
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
            data['paid'] = _('Yes') if registration.paid else ''

        data.update({field['field'].name: field['value'] for field in
                     registration.registration_information()})
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
    except (Registration.DoesNotExist, AttributeError):
        pass

    return render(request, 'events/event.html', context)


def _send_queue_mail(event):
    if (event.max_participants is not None and
        Registration.objects
                    .filter(event=event, date_cancelled=None)
                    .count() > event.max_participants):
        # Prepare email to send to the first person on the waiting
        # list
        first_waiting = (Registration.objects
                         .filter(event=event, date_cancelled=None)
                         .order_by('date')[event.max_participants])
        first_waiting_member = first_waiting.member

        text_template = get_template('events/email.txt')

        with translation.override(first_waiting_member.language):
            subject = _("[THALIA] Notification about your "
                        "registration for '{}'").format(
                event.title)
            text_message = text_template.render({
                'event': event,
                'reg': first_waiting,
                'member': first_waiting_member
            })

            EmailMessage(
                subject,
                text_message,
                to=[first_waiting_member.user.email]
            ).send()


def _show_registration_fields(request, event, reg, action):
    form = FieldsForm(registration=reg)
    if request.POST:
        form = FieldsForm(request.POST, registration=reg)
        if form.is_valid():
            reg.save()
            form_field_values = form.field_values()
            for field in form_field_values:
                if (field['field'].type ==
                        RegistrationInformationField.INTEGER_FIELD and
                        field['value'] is None):
                    field['value'] = 0
                field['field'].set_value_for(reg,
                                             field['value'])

    return render(request, 'events/event_fields.html',
                  {'event': event, 'form': form, 'action': action})


def _registration_register(request, event, reg):
    if reg is None:
        reg = Registration()
        reg.event = event
        reg.member = request.user.member
        messages.success(request, _("Registration successful."))
        if event.has_fields():
            return _show_registration_fields(request, event, reg, 'register')
        else:
            reg.save()
    elif reg.date_cancelled is not None:
        if reg.is_late_cancellation():
            messages.error(request, _("You cannot re-register anymore since "
                                      "you've cancelled after the deadline."))
        else:
            reg.date = timezone.now()
            reg.date_cancelled = None
            messages.success(request, _("Registration successful."))
            if event.has_fields():
                return _show_registration_fields(request, event, reg,
                                                 'register')
            else:
                reg.save()
    elif not reg.member.can_attend_events:
        messages.error(request, _("You may not register"))
    else:
        storage = messages.get_messages(request)
        was_success = False
        for message in storage:
            was_success = message.message == _("Registration successful.")
        storage.used = False
        if not was_success:
            messages.error(request, _("You were already registered."))

    return redirect(event)


def _registration_update(request, event, reg):
    if not event.has_fields():
        return redirect(event)
    if reg is None:
        messages.error(request, _("You are not registered for this event."))
        return redirect(event)

    return _show_registration_fields(request, event, reg, 'update')


def _registration_cancel(request, event, reg):
    if reg is None or reg.date_cancelled is not None:
        messages.error(request, _("You are not registered for this event."))
    else:
        # Note that this doesn't remove the values for the
        # information fields that the user entered upon registering.
        # But this is regarded as a feature, not a bug. Especially
        # since the values will still appear in the backend.
        reg.date_cancelled = timezone.now()
        reg.save()

        _send_queue_mail(event)

        messages.success(request, _("Registration successfully cancelled."))

    return redirect(event)


@login_required
def registration(request, event_id, action=None):
    event = get_object_or_404(
        Event.objects.filter(published=True),
        pk=event_id
    )

    if (event.status != Event.REGISTRATION_NOT_NEEDED and
            request.user.member.current_membership is not None and
            request.user.member.can_attend_events):
        try:
            reg = Registration.objects.get(
                event=event,
                member=request.user.member
            )
        except Registration.DoesNotExist:
            reg = None

        if request.method.lower() == 'post':
            if action == 'register' and (
                event.status == Event.REGISTRATION_OPEN or
                event.status == Event.REGISTRATION_OPEN_NO_CANCEL
            ):
                return _registration_register(request, event, reg)
            elif (action == 'update' and
                  (event.status == Event.REGISTRATION_OPEN or
                   event.status == Event.REGISTRATION_OPEN_NO_CANCEL)):
                return _registration_update(request, event, reg)
            elif action == 'cancel':
                return _registration_cancel(request, event, reg)

    return redirect(event)


@staff_member_required
@permission_required('events.change_event')
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
        present=True, paid=True)

    return HttpResponseRedirect('/events/admin/{}'.format(event_id))
