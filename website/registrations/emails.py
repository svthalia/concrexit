"""The emails defined by the registrations package."""
from typing import Union

from django.conf import settings
from django.template.defaultfilters import floatformat
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from registrations.models import Registration, Renewal
from utils.snippets import send_email


def send_registration_email_confirmation(registration: Registration) -> None:
    """Send the email confirmation message.

    :param registration: the registration entry
    """
    send_email(
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


def send_registration_accepted_message(registration: Registration) -> None:
    """Send the registration acceptance email.

    :param registration: the registration entry
    """
    send_email(
        registration.email,
        _("Registration accepted"),
        "registrations/email/registration_accepted.txt",
        {
            "name": registration.get_full_name(),
            "fees": floatformat(registration.contribution, 2),
        },
    )


def send_registration_rejected_message(registration: Registration) -> None:
    """Send the registration rejection email.

    :param registration: the registration entry
    """
    send_email(
        registration.email,
        _("Registration rejected"),
        "registrations/email/registration_rejected.txt",
        {"name": registration.get_full_name()},
    )


def send_new_registration_board_message(registration: Registration) -> None:
    """Send a notification to the board about a new registration.

    :param registration: the registration entry
    """
    send_email(
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


def send_renewal_accepted_message(renewal: Renewal) -> None:
    """Send the renewal acceptation email.

    :param renewal: the renewal entry
    """
    send_email(
        renewal.member.email,
        _("Renewal accepted"),
        "registrations/email/renewal_accepted.txt",
        {
            "name": renewal.member.get_full_name(),
            "fees": floatformat(renewal.contribution, 2),
            "thalia_pay_enabled": settings.THALIA_PAY_ENABLED_PAYMENT_METHOD,
            "url": (
                settings.BASE_URL
                + reverse(
                    "registrations:renew",
                )
            ),
        },
    )


def send_renewal_rejected_message(renewal: Renewal) -> None:
    """Send the renewal rejection email.

    :param renewal: the renewal entry
    """
    send_email(
        renewal.member.email,
        _("Renewal rejected"),
        "registrations/email/renewal_rejected.txt",
        {"name": renewal.member.get_full_name()},
    )


def send_renewal_complete_message(renewal: Renewal) -> None:
    """Send the email completing the renewal.

    :param renewal: the renewal entry
    """
    send_email(
        renewal.member.email,
        _("Renewal successful"),
        "registrations/email/renewal_complete.txt",
        {"name": renewal.member.get_full_name()},
    )


def send_new_renewal_board_message(renewal: Renewal) -> None:
    """Send a notification to the board about a new renewal.

    :param renewal: the renewal entry
    """
    send_email(
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
    """Send a notification to the user with information about references.

    These are required for benefactors who have not been a Thalia member
    and do not work for iCIS

    :param entry: the registration or renewal entry
    """
    if type(entry).__name__ == "Registration":
        email = entry.email
        name = entry.get_full_name()
    else:
        email = entry.member.email
        name = entry.member.get_full_name()

    send_email(
        email,
        _("Information about references"),
        "registrations/email/references_information.txt",
        {
            "name": name,
            "reference_link": (
                settings.BASE_URL + reverse("registrations:reference", args=[entry.pk])
            ),
        },
    )
