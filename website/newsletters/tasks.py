from django.utils import timezone

from celery import shared_task

from newsletters import services
from newsletters.models import Newsletter


@shared_task
def send_planned_newsletters():
    newsletters = Newsletter.objects.filter(send_date__lte=timezone.now(), sent=False)
    for n in newsletters:
        services.send_newsletter(n)
