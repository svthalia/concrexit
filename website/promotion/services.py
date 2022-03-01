from django.utils import timezone
from promotion.models import PromotionRequest

def get_new_requests(end_date):
    start_date = end_date - timezone.timedelta(weeks=1)
    base_requests = PromotionRequest.objects.filter(created_at__range=(start_date, end_date))
    return base_requests


def get_upcoming_requests(start_date):
    end_date = start_date + timezone.timedelta(weeks=1)
    base_requests = PromotionRequest.objects.filter(publish_date__range=(start_date, end_date))
    return base_requests