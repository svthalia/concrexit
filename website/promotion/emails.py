"""The emails defined by the promotion request package."""
import logging

from django.conf import settings

from promotion.models import PromotionRequest
from utils.snippets import send_email

logger = logging.getLogger(__name__)


def send_weekly_overview():

    new_requests = PromotionRequest.new_requests.all()
    upcoming_requests = PromotionRequest.upcoming_requests.all()

    from_email = settings.PROMO_REQUEST_NOTIFICATION_ADDRESS
    subject = "[PROMO] Weekly request overview"
    context = {
        "new_requests": new_requests,
        "upcoming_requests": upcoming_requests,
    }

    send_email(
        to=from_email,
        subject=subject,
        body_template="requests/weekly_overview.txt",
        context=context,
    )
