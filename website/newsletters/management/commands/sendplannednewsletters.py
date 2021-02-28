from django.core.management.base import BaseCommand
from django.utils import timezone

from newsletters import services
from newsletters.models import Newsletter


class Command(BaseCommand):
    """This command needs to be executed at least once a week when the newsletter is planned. It will send it automatically."""

    def handle(self, *args, **options):
        newsletters = Newsletter.objects.filter(
            send_date__lte=timezone.now(), sent=False
        )
        for n in newsletters:
            services.send_newsletter(n)
