"""The emails defined by the events package."""
from django.conf import settings

from utils.snippets import send_email


def notify_first_waiting(event):
    """Send an email to the first person on the waiting list when someone cancels their registration.

    :param event: the event
    """
    if (
        event.max_participants is not None
        and event.eventregistration_set.filter(date_cancelled=None).count()
        > event.max_participants
    ):
        # Prepare email to send to the first person on the waiting list
        first_waiting = event.eventregistration_set.filter(
            date_cancelled=None
        ).order_by("date")[event.max_participants]

        organiser_emails = [
            organiser.contact_address for organiser in event.organisers.all()
        ]

        send_email(
            to=[first_waiting.email],
            subject=f"Notification about your registration for '{event.title}'",
            txt_template="events/email/member_email.txt",
            html_template="events/email/member_email.html",
            context={
                "event": event,
                "registration": first_waiting,
                "name": first_waiting.name or first_waiting.member.first_name,
                "base_url": settings.BASE_URL,
                "organisers": organiser_emails,
            },
        )


def notify_organiser(event, registration):
    """Send an email to the organiser of the event if someone cancels their registration.

    :param event: the event
    :param registration: the registration that was cancelled
    """
    if not event.organisers.exists():
        return

    send_email(
        to=[organiser.contact_address for organiser in event.organisers.all()],
        subject=f"Registration for {event.title} cancelled by member",
        txt_template="events/email/organiser_email.txt",
        html_template="events/email/organiser_email.html",
        context={"event": event, "registration": registration},
    )


def notify_waiting(event, registration):
    organiser_emails = [
        organiser.contact_address for organiser in event.organisers.all()
    ]

    send_email(
        to=[registration.email],
        subject=f"Notification about your registration for '{event.title}'",
        txt_template="events/email/more_places_email.txt",
        html_template="events/email/more_places_email.html",
        context={
            "event": event,
            "registration": registration,
            "name": registration.name or registration.member.first_name,
            "base_url": settings.BASE_URL,
            "organisers": organiser_emails,
        },
    )


def notify_registration(registration):
    send_email(
        to=[registration.email],
        subject=f"Registration confirmation for {registration.event.title}",
        txt_template="events/email/registration_confirmation_email.txt",
        html_template="events/email/registration_confirmation_email.html",
        context={
            "event": registration.event,
            "registration": registration,
            "name": registration.name or registration.member.first_name,
            "base_url": settings.BASE_URL,
        },
    )
