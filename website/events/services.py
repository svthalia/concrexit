from collections import OrderedDict

from django.utils import timezone
from django.utils.translation import ugettext_lazy as _, get_language

from events import emails
from events.exceptions import RegistrationError
from events.models import Registration, RegistrationInformationField
from payments.models import Payment


def is_user_registered(member, event):
    """
    Returns if the user is registered for the specified event

    :param member: the user
    :param event: the event
    :return: None if registration is not required or no member else True/False
    """
    if not event.registration_required or not member.is_authenticated:
        return None

    return event.registrations.filter(
        member=member,
        date_cancelled=None).count() > 0


def event_permissions(member, event):
    """
    Returns a dictionary with the available event permissions of the user

    :param member: the user
    :param event: the event
    :return: the permission dictionary
    """
    perms = {
        "create_registration": False,
        "cancel_registration": False,
        "update_registration": False,
    }
    if member and member.is_authenticated:
        registration = None
        try:
            registration = Registration.objects.get(
                event=event,
                member=member
            )
        except Registration.DoesNotExist:
            pass

        perms["create_registration"] = (
            (registration is None or registration.date_cancelled is not None)
            and event.registration_allowed and
            member.can_attend_events)
        perms["cancel_registration"] = (
            registration is not None and
            registration.date_cancelled is None and
            event.cancellation_allowed)
        perms["update_registration"] = (
            registration is not None and
            registration.date_cancelled is None and
            event.has_fields() and
            event.registration_allowed and
            member.can_attend_events)

    return perms


def is_organiser(member, event):
    if member and member.is_authenticated:
        if member.is_superuser or member.has_perm("events.override_organiser"):
            return True

        if event and member.has_perm('events.change_event'):
            return member.get_member_groups().filter(
                    pk=event.organiser.pk).count() != 0

    return False


def create_registration(member, event):
    """
    Creates a new user registration for an event

    :param member: the user
    :param event: the event
    :return: returns the registration if successful
    """
    if event_permissions(member, event)["create_registration"]:
        registration = None
        try:
            registration = Registration.objects.get(
                event=event,
                member=member
            )
        except Registration.DoesNotExist:
            pass

        if registration is None:
            return Registration.objects.create(
                event=event,
                member=member
            )
        elif registration.date_cancelled is not None:
            if registration.is_late_cancellation():
                raise RegistrationError(_("You cannot re-register anymore "
                                          "since you've cancelled after the "
                                          "deadline."))
            else:
                registration.date = timezone.now()
                registration.date_cancelled = None
                registration.save()

        return registration
    elif event_permissions(member, event)["cancel_registration"]:
        raise RegistrationError(_("You were already registered."))
    else:
        raise RegistrationError(_("You may not register."))


def cancel_registration(request, member, event):
    """
    Cancel a user registration for an event

    :param request: the request object
    :param member: the user
    :param event: the event
    """
    registration = None
    try:
        registration = Registration.objects.get(
            event=event,
            member=member
        )
    except Registration.DoesNotExist:
        pass

    if (event_permissions(member, event)["cancel_registration"] and
            registration):
        if registration.queue_position == 0:
            emails.notify_first_waiting(request, event)

            if (event.send_cancel_email and
                    event.after_cancel_deadline):
                emails.notify_organiser(event, registration)

        # Note that this doesn"t remove the values for the
        # information fields that the user entered upon registering.
        # But this is regarded as a feature, not a bug. Especially
        # since the values will still appear in the backend.
        registration.date_cancelled = timezone.now()
        registration.save()
    else:
        raise RegistrationError(_("You are not registered for this event."))


def update_registration(member, event, field_values):
    """
    Updates a user registration of an event

    :param member: the user
    :param event: the event
    :param field_values: values for the information fields
    """
    registration = None
    try:
        registration = Registration.objects.get(
            event=event,
            member=member
        )
    except Registration.DoesNotExist:
        pass

    if not registration:
        raise RegistrationError(_("You are not registered for this event."))

    if not event_permissions(member, event)["update_registration"]:
        return

    for field_id, field_value in field_values:
        field = RegistrationInformationField.objects.get(
            id=field_id.replace("info_field_", ""))

        if (field.type == RegistrationInformationField.INTEGER_FIELD
                and field_value is None):
            field_value = 0
        elif (field.type == RegistrationInformationField.BOOLEAN_FIELD
                and field_value is None):
            field_value = False
        elif (field.type == RegistrationInformationField.TEXT_FIELD
              and field_value is None):
            field_value = ''

        field.set_value_for(registration, field_value)


def registration_fields(request, member, event):
    """
    Returns information about the registration fields of a registration

    :param member: the user
    :param event: the event
    :return: the fields
    """
    try:
        registration = Registration.objects.get(
            event=event,
            member=member
        )
    except Registration.DoesNotExist as error:
        raise RegistrationError(
            _("You are not registered for this event.")) from error

    perms = (event_permissions(member, event)["update_registration"] or
             is_organiser(request.member, event))
    if perms and registration:
        information_fields = registration.information_fields
        fields = OrderedDict()

        for information_field in information_fields:
            field = information_field["field"]

            fields["info_field_{}".format(field.id)] = {
                "type": field.type,
                "label": getattr(field, "{}_{}".format(
                    "name",  get_language())),
                "description": getattr(field, "{}_{}".format(
                    "description", get_language())),
                "value": information_field["value"],
                "required": field.required
            }

        return fields
    else:
        raise RegistrationError(
            _("You are not allowed to update this registration."))


def update_registration_by_organiser(registration, member, data):
    if not is_organiser(member, registration.event):
        raise RegistrationError(
            _("You are not allowed to update this registration."))

    if 'payment' in data:
        if (data['payment']['type'] == Payment.NONE
                and registration.payment is not None):
            p = registration.payment
            registration.payment = None
            registration.save()
            p.delete()
        elif (data['payment']['type'] != Payment.NONE
              and registration.payment is not None):
            registration.payment.type = data['payment']['type']
            registration.payment.save()
        elif (data['payment']['type'] != Payment.NONE
              and registration.payment is None):
            registration.payment = Payment.objects.create(
                amount=registration.event.price,
                paid_by=registration.member,
                notes=(f'Event registration {registration.event.title_en}'
                       f'{registration.event.start}. '
                       f'Registration date: {registration.date}.'),
                processed_by=member,
                type=data['payment']['type']
            )

    if 'present' in data:
        registration.present = data['present']

    registration.save()
