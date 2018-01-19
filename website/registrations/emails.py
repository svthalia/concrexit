from django.core import mail
from django.template import loader
from django.template.defaultfilters import floatformat
from django.urls import reverse
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

from thaliawebsite.settings import settings

from . import models


def send_registration_email_confirmation(registration):
    with translation.override(registration.language):
        _send_email(
            registration.email,
            _('Confirm email address'),
            'registrations/email/registration_confirm_mail.txt',
            {
                'name': registration.get_full_name(),
                'confirm_link': '{}{}'.format(
                    'https://thalia.nu',
                    reverse('registrations:confirm-email',
                            args=[registration.pk])
                )
            }
        )


def send_registration_accepted_message(registration, payment):
    with translation.override(registration.language):
        _send_email(
            registration.email,
            _('Registration accepted'),
            'registrations/email/registration_accepted.txt',
            {
                'name': registration.get_full_name(),
                'fees': floatformat(payment.amount, 2)
            }
        )


def send_registration_rejected_message(registration):
    with translation.override(registration.language):
        _send_email(
            registration.email,
            _('Registration rejected'),
            'registrations/email/registration_rejected.txt',
            {
                'name': registration.get_full_name()
            }
        )


def send_new_registration_board_message(entry):
    try:
        _send_email(
            settings.BOARD_NOTIFICATION_ADDRESS,
            'New registration',
            'registrations/email/registration_board.txt',
            {
                'name': entry.registration.get_full_name(),
                'url': reverse('admin:registrations_registration_change',
                               args=[entry.registration.pk])
            }
        )
    except models.Registration.DoesNotExist:
        pass


def send_renewal_accepted_message(renewal, payment):
    with translation.override(renewal.member.profile.language):
        _send_email(
            renewal.member.email,
            _('Renewal accepted'),
            'registrations/email/renewal_accepted.txt',
            {
                'name': renewal.member.get_full_name(),
                'fees': floatformat(payment.amount, 2)
            }
        )


def send_renewal_rejected_message(renewal):
    with translation.override(renewal.member.profile.language):
        _send_email(
            renewal.member.email,
            _('Registration rejected'),
            'registrations/email/renewal_rejected.txt',
            {
                'name': renewal.member.get_full_name()
            }
        )


def send_renewal_complete_message(renewal):
    with translation.override(renewal.member.profile.language):
        _send_email(
            renewal.member.email,
            _('Renewal successful'),
            'registrations/email/renewal_complete.txt',
            {
                'name': renewal.member.get_full_name()
            }
        )


def send_new_renewal_board_message(renewal):
    _send_email(
        settings.BOARD_NOTIFICATION_ADDRESS,
        'New renewal',
        'registrations/email/renewal_board.txt',
        {
            'name': renewal.member.get_full_name(),
            'url': reverse('admin:registrations_renewal_change',
                           args=[renewal.pk])
        }
    )


def _send_email(to, subject, body_template, context):
    mail.EmailMessage(
        '[THALIA] {}'.format(subject),
        loader.render_to_string(body_template, context),
        settings.WEBSITE_FROM_ADDRESS,
        [to]
    ).send()
