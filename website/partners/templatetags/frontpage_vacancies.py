from django import template
from django.urls import reverse

from partners.models import Vacancy

register = template.Library()


@register.inclusion_tag("partners/frontpage_vacancies.html")
def render_frontpage_vacancies():
    vacancies = []

    for vacancy in Vacancy.objects.order_by("?")[:6]:
        url = f"{reverse('partners:vacancies')}#vacancy-{vacancy.id}"
        if vacancy.partner and vacancy.partner.is_active:
            url = f"{vacancy.partner.get_absolute_url()}#vacancy-{vacancy.id}"

        vacancies.append(
            {
                "title": vacancy.title,
                "company_name": vacancy.get_company_name(),
                "url": url,
            }
        )

    return {"vacancies": vacancies}
