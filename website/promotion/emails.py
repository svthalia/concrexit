"""The emails defined by the promotion request package."""
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from utils.snippets import send_email


def notify_new_promo_request(promo_request):
    send_email(
        settings.PROMO_REQUEST_NOTIFICATION_ADDRESS,
        _("[PROMO] New ") + str(promo_request),
        "requests/new_request_email.txt",
        {
            "promo_request": promo_request,
        },
    )
