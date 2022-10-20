"""The emails defined by the members package."""
import logging
from datetime import timedelta

from django.conf import settings
from django.core import mail
from django.core.mail import EmailMultiAlternatives
from django.template import loader
from django.template.defaultfilters import floatformat
from django.template.loader import get_template
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _

from members.models import Member, Membership

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
                email_body = loader.render_to_string(
                    "members/email/membership_announcement.txt",
                    {"name": member.get_full_name()},
                )
                mail.EmailMessage(
                    f"[THALIA] {_('Membership announcement')}",
                    email_body,
                    settings.DEFAULT_FROM_EMAIL,
                    [member.email],
                    bcc=[settings.BOARD_NOTIFICATION_ADDRESS],
                    connection=connection,
                ).send()

        if not dry_run:
            mail.mail_managers(
                _("Membership announcement sent"),
                loader.render_to_string(
                    "members/email/membership_announcement_notification.txt",
                    {"members": members},
                ),
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

                email_context = {
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
                    }.items()
                }
                html_template = get_template("members/email/information_check.html")
                text_template = get_template("members/email/information_check.txt")
                subject = "[THALIA] " + _("Membership information check")
                html_message = html_template.render(email_context)
                text_message = text_template.render(email_context)

                msg = EmailMultiAlternatives(
                    subject,
                    text_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [member.email],
                )
                msg.attach_alternative(html_message, "text/html")
                msg.send()

        if not dry_run:
            mail.mail_managers(
                _("Membership information check sent"),
                loader.render_to_string(
                    "members/email/information_check_notification.txt",
                    {"members": members},
                ),
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

                renewal_url = settings.BASE_URL + reverse("registrations:renew")
                email_body = loader.render_to_string(
                    "members/email/expiration_announcement.txt",
                    {
                        "name": member.get_full_name(),
                        "membership_price": floatformat(
                            settings.MEMBERSHIP_PRICES["year"], 2
                        ),
                        "renewal_url": renewal_url,
                    },
                )
                mail.EmailMessage(
                    f"[THALIA] {_('Membership expiration announcement')}",
                    email_body,
                    settings.DEFAULT_FROM_EMAIL,
                    [member.email],
                    bcc=[settings.BOARD_NOTIFICATION_ADDRESS],
                    connection=connection,
                ).send()

        if not dry_run:
            mail.mail_managers(
                _("Membership expiration announcement sent"),
                loader.render_to_string(
                    "members/email/expiration_announcement_notification.txt",
                    {"members": members},
                ),
                connection=connection,
            )


def send_welcome_message(user, password):
    """Send an email to a new mail welcoming them.

    :param user: the new user
    :param password: randomly generated password
    """
    email_body = loader.render_to_string(
        "members/email/welcome.txt",
        {
            "full_name": user.get_full_name(),
            "username": user.username,
            "password": password,
            "url": settings.BASE_URL,
        },
    )
    user.email_user(_("Welcome to Study Association Thalia"), email_body)


def send_email_change_confirmation_messages(change_request):
    """Send emails to the old and new email address of a member to confirm the email change.

    :param change_request the email change request entered by the user
    """
    member = change_request.member

    confirm_link = settings.BASE_URL + reverse(
        "members:email-change-confirm",
        args=[change_request.confirm_key],
    )
    mail.EmailMessage(
        f"[THALIA] {_('Please confirm your email change')}",
        loader.render_to_string(
            "members/email/email_change_confirm.txt",
            {
                "confirm_link": confirm_link,
                "name": member.first_name,
            },
        ),
        settings.DEFAULT_FROM_EMAIL,
        [member.email],
    ).send()

    confirm_link = settings.BASE_URL + reverse(
        "members:email-change-verify",
        args=[change_request.verify_key],
    )
    mail.EmailMessage(
        f"[THALIA] {_('Please verify your email address')}",
        loader.render_to_string(
            "members/email/email_change_verify.txt",
            {
                "confirm_link": confirm_link,
                "name": member.first_name,
            },
        ),
        settings.DEFAULT_FROM_EMAIL,
        [change_request.email],
    ).send()


def send_email_change_completion_message(change_request):
    """Send email to the member to confirm the email change.

    :param change_request the email change request entered by the user
    """
    change_request.member.email_user(
        f"[THALIA] {_('Your email address has been changed')}",
        loader.render_to_string(
            "members/email/email_change_completed.txt",
            {"name": change_request.member.first_name},
        ),
    )
