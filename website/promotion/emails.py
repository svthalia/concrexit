"""The emails defined by the promotion request package."""
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from utils.snippets import send_email


def notify_new_request(request):
    if request.event:
        send_email(
            settings.PROMO_REQUEST_NOTIFICATION_ADDRESS,
            _(f"[THALIA][PROMO] New promotion request for {request.event}"),
            "requests/new_request_email.txt",
            {"event": request,},
        )
    else:
        send_email(
            settings.PROMO_REQUEST_NOTIFICATION_ADDRESS,
            _(f"[THALIA][PROMO] New promotion request"),
            "requests/new_request_email_no_event.txt",
            {"request": request,},
        )
