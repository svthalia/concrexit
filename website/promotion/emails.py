"""The emails defined by the promotion request package."""
import logging
from smtplib import SMTPException

from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import translation, timezone
from django.template.loader import get_template
from django.core import mail
from django.core.mail import EmailMultiAlternatives

from promotion import services

logger = logging.getLogger(__name__)

def send_weekly_overview():

    new_requests = services.get_new_requests(timezone.localtime())
    upcoming_requests = services.get_upcoming_requests(timezone.localdate())

    from_email = settings.PROMO_REQUEST_NOTIFICATION_ADDRESS
    text_template = get_template("requests/weekly_overview.txt")

    with mail.get_connection() as connection:
        language = ("en", "English")
        translation.activate(language[0])

        subject = "[PROMO] Weekly request overview"

        context = {
            "new_requests": new_requests,
            "upcoming_requests": upcoming_requests,
            "lang_code": language[0],
        }

        text_message = text_template.render(context)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            to=[from_email],
            from_email=from_email,
            connection=connection,
        )

        try:
            msg.send()
            logger.info("Sent weekly overview")
        except SMTPException:
            logger.exception("Failed to send the weekly overview")

        translation.deactivate()


send_weekly_overview()