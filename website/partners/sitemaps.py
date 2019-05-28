from django.contrib import sitemaps
from django.urls import reverse

from . import models


class StaticViewSitemap(sitemaps.Sitemap):
    """Sitemap generator for static partner views."""

    changefreq = 'daily'

    def items(self):
        """Return static partner view names."""
        return ['partners:index', 'partners:vacancies']

    def location(self, item):
        """Return view url."""
        return reverse(item)


class PartnerSitemap(sitemaps.Sitemap):
    """Sitemap generator for partners."""

    def items(self):
        """Return all active partners."""
        return models.Partner.objects.filter(is_active=True)

    def location(self, item):
        """Return the partner url."""
        return item.get_absolute_url()


class VacancySitemap(sitemaps.Sitemap):
    """Sitemap generator for vacancies."""

    def items(self):
        """Return all vacancies."""
        return models.Vacancy.objects.all()

    def location(self, item):
        """Return the vacancy url."""
        return item.get_absolute_url()


sitemap = {
    'partners-static': StaticViewSitemap,
    'partners-partners': PartnerSitemap,
    'partners-vacancies': VacancySitemap,
}
