from django.core import mail
from django.template import loader
from django.utils import translation
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
