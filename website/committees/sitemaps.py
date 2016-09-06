from django.contrib import sitemaps
from django.urls import reverse

from . import models


class StaticViewSitemap(sitemaps.Sitemap):
    priority = 0.5
    changefreq = 'daily'

    def items(self):
        return ['committees:committees', 'committees:boards']

    def location(self, item):
        return reverse(item)


class CommitteeSitemap(sitemaps.Sitemap):

    def items(self):
        return models.Committee.active_committees.all()

    def location(self, item):
        return item.get_absolute_url()


class BoardSitemap(sitemaps.Sitemap):
    changefreq = 'yearly'

    def items(self):
        return models.Board.objects.all()

    def location(self, item):
        return item.get_absolute_url()


sitemap = {
    'committees-static': StaticViewSitemap,
    'committees-committees': CommitteeSitemap,
    'committees-boards': BoardSitemap,
}
