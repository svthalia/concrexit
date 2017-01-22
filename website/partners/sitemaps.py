from django.contrib import sitemaps
from django.urls import reverse

from . import models


class StaticViewSitemap(sitemaps.Sitemap):
    changefreq = 'daily'

    def items(self):
        return ['partners:index', 'partners:vacancies']

    def location(self, item):
        return reverse(item)


class PartnerSitemap(sitemaps.Sitemap):

    def items(self):
        return models.Partner.objects.filter(is_active=True)

    def location(self, item):
        return item.get_absolute_url()


class VacancySitemap(sitemaps.Sitemap):
    def items(self):
        return models.Vacancy.objects.all()

    def location(self, item):
        return item.get_absolute_url()


sitemap = {
    'partners-static': StaticViewSitemap,
    'partners-partners': PartnerSitemap,
    'partners-vacancies': VacancySitemap,
}
