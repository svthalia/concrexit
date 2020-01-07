"""The emails defined by the registrations package"""
from typing import Union

from django.conf import settings
from django.core import mail
from django.template import loader
from django.template.defaultfilters import floatformat
from django.urls import reverse
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

from payments.models import Payment
from registrations.models import Registration, Renewal


def send_registration_email_confirmation(registration: Registration) -> None:
    """
    Send the email confirmation message

    :param registration: the registration entry
    """
    with translation.override(registration.language):
        _send_email(
            registration.email,
            _("Confirm email address"),
            "registrations/email/registration_confirm_mail.txt",
            {
                "name": registration.get_full_name(),
                "confirm_link": (
                    settings.BASE_URL
                    + reverse("registrations:confirm-email", args=[registration.pk])
                ),
            },
        )


def send_registration_accepted_message(
    registration: Registration, payment: Payment
) -> None:
    """
    Send the registration acceptance email

    :param registration: the registration entry
    :param payment: the payment entry
    """
    with translation.override(registration.language):
        _send_email(
            registration.email,
            _("Registration accepted"),
            "registrations/email/registration_accepted.txt",
            {
                "name": registration.get_full_name(),
                "fees": floatformat(payment.amount, 2),
            },
        )


def send_registration_rejected_message(registration: Registration) -> None:
    """
    Send the registration rejection email

    :param registration: the registration entry
    """
    with translation.override(registration.language):
        _send_email(
            registration.email,
            _("Registration rejected"),
            "registrations/email/registration_rejected.txt",
            {"name": registration.get_full_name()},
        )


def send_new_registration_board_message(registration: Registration) -> None:
    """
    Send a notification to the board about a new registration

    :param registration: the registration entry
    """
    _send_email(
        settings.BOARD_NOTIFICATION_ADDRESS,
        "New registration",
        "registrations/email/registration_board.txt",
        {
            "name": registration.get_full_name(),
            "url": (
                settings.BASE_URL
                + reverse(
                    "admin:registrations_registration_change", args=[registration.pk]
                )
            ),
        },
    )


def send_renewal_accepted_message(renewal: Renewal, payment: Payment) -> None:
    """
    Send the renewal acceptation email

    :param renewal: the renewal entry
    :param payment: the payment entry
    """
    with translation.override(renewal.member.profile.language):
        _send_email(
            renewal.member.email,
            _("Renewal accepted"),
            "registrations/email/renewal_accepted.txt",
            {
                "name": renewal.member.get_full_name(),
                "fees": floatformat(payment.amount, 2),
            },
        )


def send_renewal_rejected_message(renewal: Renewal) -> None:
    """
    Send the renewal rejection email

    :param renewal: the renewal entry
    """
    with translation.override(renewal.member.profile.language):
        _send_email(
            renewal.member.email,
            _("Renewal rejected"),
            "registrations/email/renewal_rejected.txt",
            {"name": renewal.member.get_full_name()},
        )


def send_renewal_complete_message(renewal: Renewal) -> None:
    """
    Send the email completing the renewal

    :param renewal: the renewal entry
    """
    with translation.override(renewal.member.profile.language):
        _send_email(
            renewal.member.email,
            _("Renewal successful"),
            "registrations/email/renewal_complete.txt",
            {"name": renewal.member.get_full_name()},
        )


def send_new_renewal_board_message(renewal: Renewal) -> None:
    """
    Send a notification to the board about a new renewal

    :param renewal: the renewal entry
    """
    _send_email(
        settings.BOARD_NOTIFICATION_ADDRESS,
        "New renewal",
        "registrations/email/renewal_board.txt",
        {
            "name": renewal.member.get_full_name(),
            "url": (
                settings.BASE_URL
                + reverse("admin:registrations_renewal_change", args=[renewal.pk])
            ),
        },
    )


def send_references_information_message(entry: Union[Registration, Renewal]) -> None:
    """
    Send a notification to the user with information about references
    These are required for benefactors who have not been a Thalia member
    and do not work for iCIS

    :param entry: the registration or renewal entry
    """

    if type(entry).__name__ == "Registration":
        email = entry.email
        name = entry.get_full_name()
        language = entry.language
    else:
        email = entry.member.email
        name = entry.member.get_full_name()
        language = entry.member.profile.language

    with translation.override(language):
        _send_email(
            email,
            _("Information about references"),
            "registrations/email/references_information.txt",
            {
                "name": name,
                "reference_link": (
                    settings.BASE_URL
                    + reverse("registrations:reference", args=[entry.pk])
                ),
            },
        )


def _send_email(to: str, subject: str, body_template: str, context: dict) -> None:
    """
    Easily send an email with the right subject and a body template

    :param to: where should the email go?
    :param subject: what is the email about?
    :param body_template: what is the content of the email?
    :param context: add some context to the body
    """
    mail.EmailMessage(
        "[THALIA] {}".format(subject),
        loader.render_to_string(body_template, context),
        settings.DEFAULT_FROM_EMAIL,
        [to],
    ).send()
