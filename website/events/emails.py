"""The emails defined by the events package"""
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import get_template
from django.utils import translation
from django.utils.translation import gettext_lazy as _

from events.models import EventRegistration
from members.models import Profile


def notify_first_waiting(event):
    """
    Send an email to the first person on the waiting list
    when someone cancels their registration

    :param event: the event
    """
    if (
        event.max_participants is not None
        and EventRegistration.objects.filter(event=event, date_cancelled=None).count()
        > event.max_participants
    ):
        # Prepare email to send to the first person on the waiting list
        first_waiting = EventRegistration.objects.filter(
            event=event, date_cancelled=None
        ).order_by("date")[event.max_participants]
        first_waiting_member = first_waiting.member

        text_template = get_template("events/member_email.txt")

        if first_waiting_member.profile:
            language = first_waiting_member.profile.language
        else:
            language = Profile._meta.get_field("language").default

        with translation.override(language):
            subject = _(
                "[THALIA] Notification about your registration for '{}'"
            ).format(event.title)
            text_message = text_template.render(
                {
                    "event": event,
                    "registration": first_waiting,
                    "member": first_waiting_member,
                    "base_url": settings.BASE_URL,
                }
            )

            EmailMessage(subject, text_message, to=[first_waiting_member.email]).send()


def notify_organiser(event, registration):
    """
    Send an email to the organiser of the event if
    someone cancels their registration

    :param event: the event
    :param registration: the registration that was cancelled
    """
    if event.organiser is None or event.organiser.contact_mailinglist is None:
        return

    text_template = get_template("events/organiser_email.txt")
    subject = "Registration for {} cancelled by member".format(event.title)
    text_message = text_template.render({"event": event, "registration": registration})

    EmailMessage(
        subject,
        text_message,
        to=[event.organiser.contact_mailinglist.name + "@thalia.nu"],
    ).send()
