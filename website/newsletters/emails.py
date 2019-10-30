"""The emails defined by the newsletters package"""
import logging
from smtplib import SMTPException

from django.conf import settings
from django.core import mail
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.utils import translation, timezone
from django.utils.timezone import make_aware

from members.models import Member
from newsletters import services
from partners.models import Partner

logger = logging.getLogger(__name__)


def send_newsletter(newsletter):
    """
    Sends the newsletter as HTML and plaintext email

    :param newsletter: the newsletter to be send
    """
    events = None
    if newsletter.date:
        datetime = make_aware(timezone.datetime(
            year=newsletter.date.year,
            month=newsletter.date.month,
            day=newsletter.date.day,
        )) if newsletter.date else None
        events = services.get_agenda(datetime)

    from_email = settings.NEWSLETTER_FROM_ADDRESS
    html_template = get_template('newsletters/email.html')
    text_template = get_template('newsletters/email.txt')

    main_partner = Partner.objects.filter(is_main_partner=True).first()
    local_partner = Partner.objects.filter(is_local_partner=True).first()

    with mail.get_connection() as connection:
        for language in settings.LANGUAGES:
            translation.activate(language[0])

            members = Member.current_members.all().filter(
                profile__receive_newsletter=True,
                profile__language=language[0]
            )

            subject = '[THALIA] ' + newsletter.title

            context = {
                'newsletter': newsletter,
                'agenda_events': events,
                'main_partner': main_partner,
                'local_partner': local_partner,
                'lang_code': language[0]
            }

            html_message = html_template.render(context)
            text_message = text_template.render(context)

            services.write_to_file(newsletter.pk, language[0], html_message)

            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_message,
                from_email=from_email,
                connection=connection
            )
            msg.attach_alternative(html_message, "text/html")

            for member in members:
                if not member.email:
                    return

                msg.to = [member.email]
                try:
                    msg.send()
                    logger.info('Sent newsletter to %s (%s)',
                                member.get_full_name(),
                                member.email)
                except SMTPException as e:
                    logger.error('Failed to send the newsletter to %s (%s)',
                                 member.get_full_name(),
                                 member.email, e)

            translation.deactivate()
