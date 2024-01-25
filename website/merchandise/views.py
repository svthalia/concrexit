"""The views for the merchandise package."""
from django.http import Http404
from django.shortcuts import render

from merchandise.models import MerchandiseItem


def index(request):
    """Render the index view.

    :param request: the request object
    :return: the response
    """
    items = MerchandiseItem.objects.all()

    return render(request, "merchandise/index.html", {"items": items})


def product_page(request, id):
    try:
        product = MerchandiseItem.objects.get(pk=id)
    except MerchandiseItem.DoesNotExist:
        raise Http404(
            "This item may not exists, or is removed. Please check if the link is correct!"
        )

    return render(request, "merchandise/product_page.html", {"product": product})
