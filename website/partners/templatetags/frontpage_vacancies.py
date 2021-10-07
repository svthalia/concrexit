from django import template
from django.urls import reverse

from partners.models import Vacancy

register = template.Library()


@register.inclusion_tag("partners/frontpage_vacancies.html")
def render_frontpage_vacancies():
    vacancies = []

    for vacancy in Vacancy.objects.order_by("?")[:6]:
        url = "{}#vacancy-{}".format(reverse("partners:vacancies"), vacancy.id)
        if vacancy.partner:
            url = "{}#vacancy-{}".format(vacancy.partner.get_absolute_url(), vacancy.id)

        vacancies.append(
            {
                "title": vacancy.title,
                "company_name": vacancy.get_company_name(),
                "url": url,
            }
        )

    return {"vacancies": vacancies}
