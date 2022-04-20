"""The emails defined by the promotion request package."""
import logging
from smtplib import SMTPException

from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import translation, timezone
from utils import send_email
from django.template.loader import get_template
from django.core import mail
from django.core.mail import EmailMultiAlternatives

from promotion import services
from website.promotion.models import PromotionRequest

logger = logging.getLogger(__name__)

def send_weekly_overview():

    new_requests = PromotionRequest.new_requests.all()
    upcoming_requests = PromotionRequest.upcoming_requests.all()

    from_email = settings.PROMO_REQUEST_NOTIFICATION_ADDRESS
    text_template = get_template("requests/weekly_overview.txt")
    subject = "[PROMO] Weekly request overview"
    context = {
        "new_requests": new_requests,
        "upcoming_requests": upcoming_requests,
    }

    send_email(
        to=from_email, 
        subject=subject,
        body_template=text_template,
        context=context,
    )