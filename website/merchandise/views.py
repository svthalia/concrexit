"""The views for the merchandise package."""
from django.shortcuts import render

from merchandise.models import MerchandiseItem


def index(request):
    """Render the index view.

    :param request: the request object
    :return: the response
    """
    items = MerchandiseItem.objects.all()

    return render(request, "merchandise/index.html", {"items": items})


def select_product(items, id):
    for item in items:
        if item.id == id:
            return item
    return None


def product_page(request, id):
    items = MerchandiseItem.objects.all()
    product = select_product(items, id)
    if product is None:
        return render(request, "merchandise/index.html", {"items": items})
    return render(
        request, "merchandise/product_page.html", {"items": items, "product": product}
    )
