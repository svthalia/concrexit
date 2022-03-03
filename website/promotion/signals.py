from django.db.models.signals import post_save

from promotion.emails import notify_new_promo_request
from promotion.models import PromotionRequest
from utils.models.signals import suspendingreceiver


@suspendingreceiver(post_save, sender=PromotionRequest)
def notify_on_promorequest_save(sender, instance, created, **kwargs):
    """Send a notification email when a promotion request is created."""
    if created:
        notify_new_promo_request(instance)
