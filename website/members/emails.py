"""The emails defined by the members package."""
import logging
from datetime import timedelta

from django.conf import settings
from django.core import mail
from django.template.defaultfilters import floatformat
from django.urls import reverse
from django.utils import timezone

from members.models import Member, Membership
from utils.snippets import send_email

logger = logging.getLogger(__name__)


def send_membership_announcement(dry_run=False):
    """Send an email to all members with a never ending membership excluding honorary members.

    :param dry_run: does not really send emails if True
    """
    members = (
        Member.current_members.filter(membership__since__lt=timezone.now())
        .filter(membership__until__isnull=True)
        .exclude(membership__type=Membership.HONORARY)
        .exclude(email="")
        .distinct()
    )

    with mail.get_connection() as connection:
        for member in members:
            logger.info("Sent email to %s (%s)", member.get_full_name(), member.email)
            if not dry_run:
                send_email(
                    to=[member.email],
                    subject="Membership announcement",
                    txt_template="members/email/membership_announcement.txt",
                    html_template="members/email/membership_announcement.html",
                    context={"name": member.get_full_name()},
                    connection=connection,
                )

        if not dry_run:
            send_email(
                to=[settings.BOARD_NOTIFICATION_ADDRESS],
                subject="Membership announcement sent",
                txt_template="members/email/membership_announcement_notification.txt",
                html_template="members/email/membership_announcement_notification.html",
                context={"members": members},
                connection=connection,
            )


def send_information_request(dry_run=False):
    """Send an email to all members to have them check their personal information.

    :param dry_run: does not really send emails if True
    """
    members = Member.current_members.all().exclude(email="")

    with mail.get_connection() as connection:
        for member in members:
            logger.info("Sent email to %s (%s)", member.get_full_name(), member.email)
            if not dry_run:
                send_email(
                    to=[member.email],
                    subject="Membership information check",
                    txt_template="members/email/information_check.txt",
                    html_template="members/email/information_check.html",
                    connection=connection,
                    context={
                        k: x if x else ""
                        for k, x in {
                            "name": member.first_name,
                            "username": member.username,
                            "full_name": member.get_full_name(),
                            "address_street": member.profile.address_street,
                            "address_street2": member.profile.address_street2,
                            "address_postal_code": member.profile.address_postal_code,
                            "address_city": member.profile.address_city,
                            "address_country": member.profile.get_address_country_display(),
                            "phone_number": member.profile.phone_number,
                            "birthday": member.profile.birthday,
                            "email": member.email,
                            "student_number": member.profile.student_number,
                            "starting_year": member.profile.starting_year,
                            "programme": member.profile.get_programme_display(),
                            "base_url": settings.BASE_URL,
                        }.items()
                    },
                )

        if not dry_run:
            send_email(
                to=[settings.BOARD_NOTIFICATION_ADDRESS],
                subject="Membership information check sent",
                txt_template="members/email/information_check_notification.txt",
                html_template="members/email/information_check_notification.html",
                context={"members": members},
                connection=connection,
            )


def send_expiration_announcement(dry_run=False):
    """Send an email to all members whose membership will end in the next 31 days to warn them about this.

    :param dry_run: does not really send emails if True
    """
    expiry_date = timezone.now() + timedelta(days=31)
    members = (
        Member.current_members.filter(membership__until__lte=expiry_date)
        .exclude(membership__until__isnull=True)
        .exclude(email="")
        .distinct()
    )

    with mail.get_connection() as connection:
        for member in members:
            logger.info("Sent email to %s (%s)", member.get_full_name(), member.email)
            if not dry_run:
                send_email(
                    to=[member.email],
                    subject="Membership expiration announcement",
                    txt_template="members/email/expiration_announcement.txt",
                    html_template="members/email/expiration_announcement.html",
                    connection=connection,
                    context={
                        "name": member.get_full_name(),
                        "membership_price": floatformat(
                            settings.MEMBERSHIP_PRICES["year"], 2
                        ),
                        "renewal_url": settings.BASE_URL
                        + reverse("registrations:renew"),
                    },
                )

        if not dry_run:
            send_email(
                to=[settings.BOARD_NOTIFICATION_ADDRESS],
                subject="Membership expiration announcement sent",
                txt_template="members/email/expiration_announcement_notification.txt",
                html_template="members/email/expiration_announcement_notification.html",
                connection=connection,
                context={"members": members},
            )


def send_welcome_message(user, password):
    """Send an email to a new user welcoming them.

    :param user: the new user
    :param password: randomly generated password
    """
    send_email(
        to=[user.email],
        subject="Welcome to Study Association Thalia",
        txt_template="members/email/welcome.txt",
        html_template="members/email/welcome.html",
        context={
            "full_name": user.get_full_name(),
            "username": user.username,
            "password": password,
            "url": settings.BASE_URL,
            "base_url": settings.BASE_URL,
        },
    )


def send_email_change_confirmation_messages(change_request):
    """Send emails to the old and new email address of a member to confirm the email change.

    :param change_request the email change request entered by the user
    """
    member = change_request.member

    confirm_link = settings.BASE_URL + reverse(
        "members:email-change-confirm",
        args=[change_request.confirm_key],
    )
    send_email(
        to=[member.email],
        subject="Please confirm your email change",
        txt_template="members/email/email_change_confirm.txt",
        html_template="members/email/email_change_confirm.html",
        context={
            "confirm_link": confirm_link,
            "name": member.first_name,
        },
    )

    confirm_link = settings.BASE_URL + reverse(
        "members:email-change-verify",
        args=[change_request.verify_key],
    )
    send_email(
        to=[change_request.email],
        subject="Please verify your email address",
        txt_template="members/email/email_change_verify.txt",
        html_template="members/email/email_change_verify.html",
        context={
            "confirm_link": confirm_link,
            "name": member.first_name,
        },
    )


def send_email_change_completion_message(change_request):
    """Send email to the member to confirm the email change.

    :param change_request the email change request entered by the user
    """
    send_email(
        to=[change_request.member.email],
        subject="Your email address has been changed",
        txt_template="members/email/email_change_completed.txt",
        html_template="members/email/email_change_completed.html",
        context={
            "name": change_request.member.first_name,
        },
    )
