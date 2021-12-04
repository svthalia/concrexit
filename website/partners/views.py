from random import random

from django.shortcuts import get_object_or_404, render

from partners.models import Partner, Vacancy, VacancyCategory


def index(request):
    """View to show overview page of partners."""
    partners = Partner.objects.filter(
        is_active=True, is_main_partner=False, is_local_partner=False
    )
    main_partner = Partner.objects.filter(is_main_partner=True).first()
    local_partners = Partner.objects.filter(is_local_partner=True)

    context = {
        "main_partner": main_partner,
        "local_partners": local_partners,
        "partners": sorted(partners, key=lambda x: random()),
    }
    return render(request, "partners/index.html", context)


def partner(request, slug):
    """View to show partner page."""
    obj = get_object_or_404(Partner, slug=slug, is_active=True)
    context = {
        "partner": obj,
        "vacancies": Vacancy.objects.filter(partner=obj),
    }
    return render(request, "partners/partner.html", context)


def vacancies(request):
    """View to show vacancies."""
    context = {
        "vacancies": Vacancy.objects.order_by("?"),
        "categories": VacancyCategory.objects.all(),
    }

    return render(request, "partners/vacancies.html", context)
