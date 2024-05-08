"""The emails defined by the registrations package."""

from django.conf import settings
from django.template.defaultfilters import floatformat
from django.urls import reverse

from registrations.models import Registration, Renewal
from utils.snippets import send_email


def send_registration_email_confirmation(registration: Registration) -> None:
    """Send the email confirmation message.

    :param registration: the registration entry
    """
    send_email(
        to=[registration.email],
        subject="Confirm email address",
        txt_template="registrations/email/registration_confirm_mail.txt",
        html_template="registrations/email/registration_confirm_mail.html",
        context={
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
        to=[registration.email],
        subject="Registration accepted",
        txt_template="registrations/email/registration_accepted.txt",
        html_template="registrations/email/registration_accepted.html",
        context={
            "name": registration.get_full_name(),
            "fees": floatformat(registration.contribution, 2),
        },
    )


def send_registration_rejected_message(registration: Registration) -> None:
    """Send the registration rejection email.

    :param registration: the registration entry
    """
    send_email(
        to=[registration.email],
        subject="Registration rejected",
        txt_template="registrations/email/registration_rejected.txt",
        html_template="registrations/email/registration_rejected.html",
        context={"name": registration.get_full_name()},
    )


def send_new_registration_board_message(registration: Registration) -> None:
    """Send a notification to the board about a new registration.

    :param registration: the registration entry
    """
    send_email(
        to=[settings.BOARD_NOTIFICATION_ADDRESS],
        subject="New registration",
        txt_template="registrations/email/registration_board.txt",
        html_template="registrations/email/registration_board.html",
        context={
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
        to=[renewal.member.email],
        subject="Renewal accepted",
        txt_template="registrations/email/renewal_accepted.txt",
        html_template="registrations/email/renewal_accepted.html",
        context={
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
        to=[renewal.member.email],
        subject="Renewal rejected",
        txt_template="registrations/email/renewal_rejected.txt",
        html_template="registrations/email/renewal_rejected.html",
        context={"name": renewal.member.get_full_name()},
    )


def send_renewal_complete_message(renewal: Renewal) -> None:
    """Send the email completing the renewal.

    :param renewal: the renewal entry
    """
    send_email(
        to=[renewal.member.email],
        subject="Renewal successful",
        txt_template="registrations/email/renewal_complete.txt",
        html_template="registrations/email/renewal_complete.html",
        context={"name": renewal.member.get_full_name()},
    )


def send_new_renewal_board_message(renewal: Renewal) -> None:
    """Send a notification to the board about a new renewal.

    :param renewal: the renewal entry
    """
    send_email(
        to=[settings.BOARD_NOTIFICATION_ADDRESS],
        subject="New renewal",
        txt_template="registrations/email/renewal_board.txt",
        html_template="registrations/email/renewal_board.html",
        context={
            "name": renewal.member.get_full_name(),
            "url": (
                settings.BASE_URL
                + reverse("admin:registrations_renewal_change", args=[renewal.pk])
            ),
        },
    )


def send_references_information_message(entry: Registration | Renewal) -> None:
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
        to=[email],
        subject="Information about references",
        txt_template="registrations/email/references_information.txt",
        html_template="registrations/email/references_information.html",
        context={
            "name": name,
            "reference_link": (
                settings.BASE_URL + reverse("registrations:reference", args=[entry.pk])
            ),
        },
    )


def send_reminder_open_registration(registration: Registration) -> None:
    """Send a notification to the board that a registration has been open for more than one month.

    :param registration: the registration entry
    """
    send_email(
        to=[settings.BOARD_NOTIFICATION_ADDRESS],
        subject="Open registration for more than one month",
        txt_template="registrations/email/reminder_open_registration.txt",
        html_template="registrations/email/reminder_open_registration.html",
        context={
            "name": registration.get_full_name(),
            "created_at": registration.created_at,
        },
    )
