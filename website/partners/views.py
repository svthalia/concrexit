from random import random

from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from partners.models import Partner, Vacancy, VacancyCategory


def index(request):
    partners = Partner.objects.filter(is_active=True, is_main_partner=False)
    try:
        main_partner = Partner.objects.get(
            is_active=True,
            is_main_partner=True
        )
    except Partner.DoesNotExist:
        main_partner = None

    context = {
        'main_partner': main_partner,
        'partners': sorted(partners, key=lambda x: random()),
    }
    return render(request, 'partners/index.html', context)


def partner(request, slug):
    partner = get_object_or_404(Partner, slug=slug)
    context = {
        'partner': partner,
        'vacancies': Vacancy.objects.filter(partner=partner),
    }
    return render(request, 'partners/partner.html', context)


def vacancies(request):
    context = {
        'vacancies': Vacancy.objects.exclude(
            expiration_date__lte=timezone.now().date()).order_by('?'),
        'categories': VacancyCategory.objects.all(),
    }

    return render(request, 'partners/vacancies.html', context)
