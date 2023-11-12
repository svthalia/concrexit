from django.db.models.signals import post_save
from django.dispatch import receiver

from merchandise.models import MerchandiseItem, MerchandiseProduct

from .services import update_merchandise_product_list


@receiver(post_save, sender=MerchandiseProduct)
@receiver(post_save, sender=MerchandiseItem)
def update_merchandise_product_list_on_save(sender, instance, **kwargs):
    update_merchandise_product_list()
