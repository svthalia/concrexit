from django.conf import settings
from datetime import timedelta
from django.core import mail
from django.template import loader
from django.template.defaultfilters import floatformat
from django.urls import reverse
from django.utils import translation
from django.utils.datetime_safe import datetime
from django.utils.translation import ugettext as _

from members.models import Member, Membership


def send_membership_announcement(dry_run=False):
    """
    Sends an email to all members with a never ending membership
    excluding honorary members

    :param dry_run: does not really send emails if True
    """
    members = (Member.current_members
               .filter(membership__until__isnull=True)
               .exclude(membership__type=Membership.HONORARY)
               .exclude(email='')
               .distinct())

    with mail.get_connection() as connection:
        for member in members:
            print("Send email to {} ({})".format(member.get_full_name(),
                                                 member.email))
            if not dry_run:
                with translation.override(member.profile.language):
                    email_body = loader.render_to_string(
                        'members/email/membership_announcement.txt',
                        {'name': member.get_full_name()})
                    mail.EmailMessage(
                        '[THALIA] {}'.format(
                            _('Membership announcement')),
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
    """
    Sends an email to all members to have them check their personal information

    :param dry_run: does not really send emails if True
    """
    members = Member.current_members.all().exclude(email='')

    with mail.get_connection() as connection:
        for member in members:
            print("Send email to {} ({})".format(member.get_full_name(),
                                                 member.email))
            if not dry_run:
                with translation.override(member.profile.language):
                    email_body = loader.render_to_string(
                        'members/email/information_check.txt',
                        {'name': member.get_full_name(),
                         'member': member})
                    mail.EmailMessage(
                        '[THALIA] {}'.format(
                            _('Membership information check')),
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
    """
    Sends an email to all members whose membership will end in the next 31 days
    to warn them about this

    :param dry_run: does not really send emails if True
    """
    expiry_date = datetime.now() + timedelta(days=31)
    members = (Member.current_members
               .filter(membership__until__lte=expiry_date)
               .exclude(membership__until__isnull=True)
               .exclude(email='')
               .distinct())

    with mail.get_connection() as connection:
        for member in members:
            print("Send email to {} ({})".format(member.get_full_name(),
                                                 member.email))
            if not dry_run:
                with translation.override(member.profile.language):
                    email_body = loader.render_to_string(
                        'members/email/expiration_announcement.txt',
                        {
                            'name': member.get_full_name(),
                            'membership_price': floatformat(
                                settings.MEMBERSHIP_PRICES['year'], 2
                            ),
                            'renewal_url': '{}{}'.format(
                                'https://thalia.nu',
                                reverse('registrations:renew')
                            )
                        })
                    mail.EmailMessage(
                        '[THALIA] {}'.format(
                            _('Membership expiration announcement')),
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
    """
    Sends an email to a new mail welcoming them

    :param user: the new user
    :param password: randomly generated password
    :param language: selected language during registration
    """
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
    """
    Sends emails to the old and new email address of a member to
    confirm the email change

    :param change_request the email change request entered by the user
    """
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
            [member.email]
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
    """
    Sends email to the member to confirm the email change

    :param change_request the email change request entered by the user
    """
    change_request.member.email_user(
        '[THALIA] {}'.format(_('Your email address has been changed')),
        loader.render_to_string(
            'members/email/email_change_completed.txt',
            {
                'name': change_request.member.first_name
            }
        ))
