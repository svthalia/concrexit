from django.shortcuts import render

from partners.models import Partner
from random import random


def index(request):
    partners = Partner.objects.filter(is_active=True, is_main_partner=False)

    context = {
        'main_partner': Partner.objects.get(
            is_active=True,
            is_main_partner=True
        ),
        'partners': sorted(partners, key=lambda x: random()),
    }
    return render(request, 'partners/index.html', context)
