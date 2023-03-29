"""The emails defined by the promotion request package."""
import logging

from django.conf import settings

from utils.snippets import send_email

logger = logging.getLogger(__name__)


def send_sync_error(error, payment):
    send_email(
        to=[settings.TREASURER_NOTIFICATION_ADDRESS],
        subject="[MONEYBIRD] Error while syncing payment",
        txt_template="apifails/api_fail.txt",
        html_template="apifails/api_fail.html",
        context={
            "error": error,
            "payment": payment,
        },
    )
