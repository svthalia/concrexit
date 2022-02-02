"""The emails defined by the newsletters package."""
import logging
from smtplib import SMTPException

from django.conf import settings
from django.core import mail
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.utils import translation, timezone
from django.utils.timezone import make_aware

from newsletters import services
from partners.models import Partner
from thaliawebsite.context_processors import thumbnail_sizes

logger = logging.getLogger(__name__)


def send_newsletter(newsletter):
    """Send the newsletter as HTML and plaintext email.

    :param newsletter: the newsletter to be send
    """
    events = None
    if newsletter.date:
        datetime = (
            make_aware(
                timezone.datetime(
                    year=newsletter.date.year,
                    month=newsletter.date.month,
                    day=newsletter.date.day,
                )
            )
            if newsletter.date
            else None
        )
        events = services.get_agenda(datetime)

    from_email = settings.NEWSLETTER_FROM_ADDRESS
    html_template = get_template("newsletters/email.html")
    text_template = get_template("newsletters/email.txt")

    main_partner = Partner.objects.filter(is_main_partner=True).first()
    local_partners = Partner.objects.filter(is_local_partner=True)

    with mail.get_connection() as connection:
        language = ("en", "English")
        translation.activate(language[0])

        subject = "[THALIA] " + newsletter.title

        context = {
            "newsletter": newsletter,
            "agenda_events": events,
            "main_partner": main_partner,
            "local_partners": local_partners,
            "lang_code": language[0],
        }
        context.update(thumbnail_sizes(None))

        html_message = html_template.render(context)
        text_message = text_template.render(context)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            to=[f"newsletter@{settings.GSUITE_DOMAIN}"],
            from_email=from_email,
            connection=connection,
        )
        msg.attach_alternative(html_message, "text/html")

        try:
            msg.send()
            logger.info("Sent %s newsletter", language[1])
        except SMTPException:
            logger.exception("Failed to send the %s newsletter", language[1])

        translation.deactivate()
