from random import random

from django.shortcuts import get_object_or_404, render

from partners.models import Partner, Vacancy, VacancyCategory
from utils.media.services import fetch_thumbnails_db


def index(request):
    """View to show overview page of partners."""
    partners = Partner.objects.filter(
        is_active=True, is_main_partner=False, is_local_partner=False
    )
    main_partner = Partner.objects.filter(is_main_partner=True).first()
    local_partners = Partner.objects.filter(is_local_partner=True)

    fetch_thumbnails_db([p.logo for p in partners])

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
    vacancies = list(
        Vacancy.objects.order_by("?")
        .select_related("partner")
        .prefetch_related("categories")
    )
    fetch_thumbnails_db(v.get_company_logo() for v in vacancies)
    context = {
        "vacancies": vacancies,
        "categories": list(VacancyCategory.objects.all()),
    }

    return render(request, "partners/vacancies.html", context)
