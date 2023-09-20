"""The emails defined by the promotion request package."""
import logging

from django.conf import settings
from django.utils import timezone

from promotion.models import PromotionChannel, PromotionRequest
from utils.snippets import send_email

logger = logging.getLogger(__name__)


def send_weekly_overview():
    new_requests = PromotionRequest.new_requests.all()
    upcoming_requests = PromotionRequest.upcoming_requests.all()

    send_email(
        to=[settings.PROMO_REQUEST_NOTIFICATION_ADDRESS],
        subject="[PROMO] Weekly request overview",
        txt_template="promotion/email/weekly_overview.txt",
        html_template="promotion/email/weekly_overview.html",
        context={
            "new_requests": new_requests,
            "upcoming_requests": upcoming_requests,
        },
    )


def send_daily_overview():
    for email in PromotionChannel.objects.values_list(
        "publisher_reminder_email", flat=True
    ).distinct():
        daily_promotion = PromotionRequest.objects.filter(
            channel__publisher_reminder_email=email,
            status=PromotionRequest.FINISHED,
            publish_date=timezone.now(),
        ).order_by("channel__name")

        if daily_promotion.exists():
            send_email(
                to=[email],
                subject="[PROMO] Daily overview",
                txt_template="promotion/email/daily_overview.txt",
                context={
                    "daily_promotion": daily_promotion,
                },
            )
