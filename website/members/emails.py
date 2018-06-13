from django.conf import settings
from datetime import timedelta
from django.core import mail
from django.template import loader
from django.template.defaultfilters import floatformat
from django.urls import reverse
from django.utils import translation
from django.utils.datetime_safe import datetime
from django.utils.translation import ugettext as _

from members.models import Member


def send_membership_announcement(dry_run=False):
    members = (Member.current_members
               .filter(membership__until__isnull=True)
               .distinct())

    with mail.get_connection() as connection:
        for member in members:
            print("Send email to {} ({})".format(member.get_full_name(),
                                                 member.email))
            if not dry_run:
                with translation.override(member.language):
                    email_body = loader.render_to_string(
                        'members/email/membership_announcement.txt',
                        {'name': member.get_full_name()})
                    mail.EmailMessage(
                        _('Membership announcement'),
                        email_body,
                        settings.WEBSITE_FROM_ADDRESS,
                        [member.email],
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
    members = Member.current_members.all()

    with mail.get_connection() as connection:
        for member in members:
            print("Send email to {} ({})".format(member.get_full_name(),
                                                 member.email))
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
                        [member.email],
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
    members = (Member.current_members
               .filter(membership__until__lte=expiry_date)
               .distinct())

    with mail.get_connection() as connection:
        for member in members:
            print("Send email to {} ({})".format(member.get_full_name(),
                                                 member.email))
            if not dry_run:
                with translation.override(member.language):
                    email_body = loader.render_to_string(
                        'members/email/expiration_announcement.txt',
                        {'name': member.get_full_name(),
                         'membership_price': floatformat(
                             settings.MEMBERSHIP_PRICES['year'], 2
                         )})
                    mail.EmailMessage(
                        _('Membership expiration announcement'),
                        email_body,
                        settings.WEBSITE_FROM_ADDRESS,
                        [member.email],
                        bcc=[settings.BOARD_NOTIFICATION_ADDRESS],
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


def send_welcome_message(user, password, language):
    with translation.override(language):
        email_body = loader.render_to_string(
            'members/email/welcome.txt',
            {
                'full_name': user.get_full_name(),
                'username': user.username,
                'password': password
            })
        user.email_user(
            _('Welcome to Study Association Thalia'),
            email_body)


def send_email_change_confirmation_messages(change_request):
    member = change_request.member
    with translation.override(member.profile.language):
        mail.EmailMessage(
            '[THALIA] {}'.format(_('Please confirm your email change')),
            loader.render_to_string(
                'members/email/email_change_confirm.txt',
                {
                    'confirm_link': '{}{}'.format(
                        'https://thalia.nu',
                        reverse(
                            'members:email-change-confirm',
                            args=[change_request.confirm_key]
                        )),
                    'name': member.first_name
                }
            ),
            settings.WEBSITE_FROM_ADDRESS,
            [change_request.email]
        ).send()

        mail.EmailMessage(
            '[THALIA] {}'.format(_('Please verify your email address')),
            loader.render_to_string(
                'members/email/email_change_verify.txt',
                {
                    'confirm_link': '{}{}'.format(
                        'https://thalia.nu',
                        reverse(
                            'members:email-change-verify',
                            args=[change_request.verify_key]
                        )),
                    'name': member.first_name
                }
            ),
            settings.WEBSITE_FROM_ADDRESS,
            [change_request.email]
        ).send()


def send_email_change_completion_message(change_request):
    change_request.member.email_user(
        '[THALIA] {}'.format(_('Your email address has been changed')),
        loader.render_to_string(
            'members/email/email_change_completed.txt',
            {
                'name': change_request.member.first_name
            }
        ))
