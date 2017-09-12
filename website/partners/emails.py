
import datetime

from django.core.mail import EmailMessage
from django.utils import timezone

from partners.models import Vacancy
from thaliawebsite import settings


def send_vacancy_expiration_notifications(dry_run=False):
    # Select vacencies that expire in roughly a month, wherefor
    # a mail hasn't been sent yet to Mr/Mrs Extern
    expired_vacancies = Vacancy.objects.filter(
        expiration_mail_sent=False,
        expiration_date__lt=timezone.now().date() + datetime.timedelta(days=30)
    )
    for exp_vacancy in expired_vacancies:
        # Create Message
        subject = ('[WEBSITE] Vacancy \'{}\' by {} will soon expire'
                   .format(exp_vacancy.title, exp_vacancy.get_company_name()))
        text_message = ('Hello!\n\nA vacancy of {}, \'{}\' will '
                        'expire within the next 30 days. Maybe you '
                        'should contact them to negotiate a new deal. '
                        '\n\nKisses,\nThe website'
                        .format(exp_vacancy.title,
                                exp_vacancy.get_company_name()))
        recipient = settings.PARTNER_EMAIL

        if not dry_run:
            # Send Mail
            EmailMessage(
                subject,
                text_message,
                to=[recipient]
            ).send()

            # Save that mail has been sent into database
            exp_vacancy.expiration_mail_sent = True
            exp_vacancy.save()
