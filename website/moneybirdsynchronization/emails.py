"""The emails defined by the promotion request package."""
import logging

from django.conf import settings
from django.urls import reverse

from utils.snippets import send_email

logger = logging.getLogger(__name__)


def send_sync_error(error, obj):
    send_email(
        to=[settings.TREASURER_NOTIFICATION_ADDRESS],
        subject="[MONEYBIRD] Error while syncing",
        txt_template="email/moneybird_api_fail.txt",
        html_template="email/moneybird_api_fail.html",
        context={
            "error": error,
            "obj": obj,
            "url": settings.BASE_URL
            + reverse(
                f"admin:{obj._meta.app_label}_{obj._meta.model_name}_change",
                args=(obj.pk,),
            ),
        },
    )
