from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render

from pizzas.models import Product


@login_required
def index(request):
    favorite_order = get_favorite_order(request.member)
    context = {"favorite_order": favorite_order}
    return render(request, "wrapped/index.html", context)


def get_favorite_order(member):
    favorite_order = (
        Product.objects.filter(foodorder__member=member)
        .annotate(count=Count("pk"))
        .order_by("-count")
        .first()
    )

    return favorite_order
