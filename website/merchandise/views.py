from django.shortcuts import render

from .models import MerchandiseItem

def index(request):
    items = MerchandiseItem.objects.all()

    return render(request,
                  'merchandise/index.html',
                  {'items': items})
