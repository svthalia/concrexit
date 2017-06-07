from datetime import timedelta

from django.core import mail
from django.template import loader
from django.utils import translation
from django.utils.datetime_safe import datetime
from django.utils.translation import ugettext as _

from members import models
from thaliawebsite.settings import settings


def send_membership_announcement(dry_run=False):
    members = (models.Member.active_members
               .filter(user__membership__until__isnull=True))

    with mail.get_connection() as connection:
        for member in members:
            print("Send email to {} ({})".format(member.get_full_name(),
                                                 member.user.email))
            if not dry_run:
                with translation.override(member.language):
                    email_body = loader.render_to_string(
                        'members/email/membership_announcement.txt',
                        {'name': member.get_full_name()})
                    mail.EmailMessage(
                        _('Membership announcement'),
                        email_body,
                        settings.WEBSITE_FROM_ADDRESS,
                        [member.user.email],
                        bcc=[settings.BOARD_NOTIFICATION_ADDRESS],
                        connection=connection
                    ).send()

        if not dry_run:
            mail.mail_managers(
                _('Membership announcement sent'),
                loader.render_to_string(
                    'members/email/membership_announcement_notification.txt',
                    {'members': members}),
                connection=connection,
            )


def send_information_request(dry_run=False):
    members = models.Member.active_members.all()

    with mail.get_connection() as connection:
        for member in members:
            print("Send email to {} ({})".format(member.get_full_name(),
                                                 member.user.email))
            if not dry_run:
                with translation.override(member.language):
                    email_body = loader.render_to_string(
                        'members/email/information_check.txt',
                        {'name': member.get_full_name(),
                         'member': member})
                    mail.EmailMessage(
                        _('Membership information check'),
                        email_body,
                        settings.WEBSITE_FROM_ADDRESS,
                        [member.user.email],
                        bcc=[settings.BOARD_NOTIFICATION_ADDRESS],
                        connection=connection
                    ).send()

        if not dry_run:
            mail.mail_managers(
                _('Membership information check sent'),
                loader.render_to_string(
                    'members/email/information_check_notification.txt',
                    {'members': members}),
                connection=connection,
            )


def send_expiration_announcement(dry_run=False):
    expiry_date = datetime.now() + timedelta(days=31)
    members = (models.Member.active_members
               .filter(user__membership__until__lte=expiry_date))

    with mail.get_connection() as connection:
        for member in members:
            with translation.override(member.language):
                email_body = loader.render_to_string(
                    'members/email/expiration_announcement.txt',
                    {'member': member})
                mail.EmailMessage(
                    _('Membership expiration announcement'),
                    email_body,
                    settings.WEBSITE_FROM_ADDRESS,
                    [member.user.email],
                    bcc=settings.BOARD_NOTIFICATION_ADDRESS,
                    connection=connection
                ).send()

        if not dry_run:
            mail.mail_managers(
                _('Membership expiration announcement sent'),
                loader.render_to_string(
                    'members/email/expiration_announcement_notification.txt',
                    {'members': members}),
                connection=connection,
            )
