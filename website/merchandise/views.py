"""The views for the merchandise package"""
from django.shortcuts import render

from merchandise.models import MerchandiseItem


def index(request):
    """Renders the index view

    :param request: the request object
    :return: the response
    """
    items = MerchandiseItem.objects.all()

    return render(request, "merchandise/index.html", {"items": items})
