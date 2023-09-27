from django.core.management.base import BaseCommand

from promotion import emails
from promotion.models import PromotionRequest


class Command(BaseCommand):
    """Send a daily overview of promotion that has to be published."""

    def handle(self, *args, **options):
        pr = PromotionRequest.objects.first()
        emails.send_status_update(pr)
