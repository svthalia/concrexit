"""The emails defined by the newsletters package."""
import logging
from smtplib import SMTPException

from django.conf import settings
from django.utils import timezone
from django.utils.timezone import make_aware

from newsletters import services
from partners.models import Partner
from utils.snippets import send_email

logger = logging.getLogger(__name__)


def send_newsletter(newsletter):
    """Send the newsletter as HTML and plaintext email."""
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

    main_partner = Partner.objects.filter(is_main_partner=True).first()
    local_partners = services.split_local_partners()

    context = {
        "newsletter": newsletter,
        "agenda_events": events,
        "main_partner": main_partner,
        "local_partners": local_partners,
    }

    try:
        send_email(
            to=[f"newsletter@{settings.GSUITE_DOMAIN}"],
            subject=newsletter.title,
            txt_template="newsletters/email.txt",
            html_template="newsletters/email.html",
            from_email=settings.NEWSLETTER_FROM_ADDRESS,
            context=context,
        )

        logger.info("Sent newsletter")
    except SMTPException:
        logger.exception("Failed to send the newsletter")
