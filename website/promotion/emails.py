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
    for email in (
        PromotionChannel.objects.filter(publisher_reminder_email__isnull=False)
        .values_list("publisher_reminder_email", flat=True)
        .distinct()
    ):
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


def send_status_update(updated_request):
    if updated_request.event is None:
        return

    event = updated_request.event

    send_email(
        to=[organiser.contact_address for organiser in event.organisers.all()],
        subject="[PROMO] Status update",
        txt_template="promotion/email/status_update.txt",
        context={
            "updated_request": updated_request,
        },
    )


def send_daily_update_overview():
    updated_requests = PromotionRequest.objects.filter(status_updated=True)

    if updated_requests:
        send_email(
            to=[settings.PROMO_REQUEST_NOTIFICATION_ADDRESS],
            subject="[PROMO] Daily update overview",
            txt_template="promotion/email/daily_update_overview.txt",
            html_template="promotion/email/daily_update_overview.html",
            context={
                "updated_requests": updated_requests,
            },
        )
        updated_requests.update(status_updated=False)
