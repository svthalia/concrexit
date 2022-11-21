"""The emails defined by the events package."""
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import get_template
from django.utils.translation import gettext_lazy as _


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
        first_waiting_member = first_waiting.member

        text_template = get_template("events/member_email.txt")

        subject = _("[THALIA] Notification about your registration for '{}'").format(
            event.title
        )
        text_message = text_template.render(
            {
                "event": event,
                "registration": first_waiting,
                "member": first_waiting_member,
                "base_url": settings.BASE_URL,
            }
        )

        EmailMessage(subject, text_message, to=[first_waiting.email]).send()


def notify_organiser(event, registration):
    """Send an email to the organiser of the event if someone cancels their registration.

    :param event: the event
    :param registration: the registration that was cancelled
    """
    if not event.organisers.exists():
        return

    text_template = get_template("events/organiser_email.txt")
    subject = f"Registration for {event.title} cancelled by member"
    text_message = text_template.render({"event": event, "registration": registration})

    EmailMessage(
        subject,
        text_message,
        to=[
            organiser.contact_mailinglist.name + "@" + settings.SITE_DOMAIN
            for organiser in event.organisers.all()
        ],
    ).send()


def notify_waiting(event, registration):
    text_template = get_template("events/more_places_email.txt")
    subject = _("[THALIA] Notification about your registration for '{}'").format(
        event.title
    )
    text_message = text_template.render(
        {
            "event": event,
            "registration": registration,
            "member": registration.member,
            "base_url": settings.BASE_URL,
        }
    )
    EmailMessage(subject, text_message, to=[registration.email]).send()


def notify_cancelled(event, registration):
    text_template = get_template("events/less_places_email.txt")
    subject = _("[THALIA] Notification about your registration for '{}'").format(
        event.title
    )
    text_message = text_template.render(
        {
            "event": event,
            "registration": registration,
            "member": registration.member,
            "base_url": settings.BASE_URL,
        }
    )
    EmailMessage(subject, text_message, to=[registration.email]).send()
