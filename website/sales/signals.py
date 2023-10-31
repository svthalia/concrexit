from django.db.models.signals import post_save
from django.dispatch import receiver

from merchandise.models import MerchandiseItem

from .models.product import ProductList


@receiver(post_save, sender=MerchandiseItem)
def update_product_list(sender, instance, **kwargs):
    product_list = ProductList.objects.get_or_create(name="Merchandise")[0]
    product_list_products = product_list.products.all()
    merchandise_items = MerchandiseItem.objects.all()

    for merchandise_item in merchandise_items:
        if merchandise_item not in product_list_products:
            product_list.product_items.create(
                product=merchandise_item, price=merchandise_item.price
            )
