from django.contrib import sitemaps
from django.urls import reverse

from . import models


class StaticViewSitemap(sitemaps.Sitemap):
    changefreq = 'monthly'

    def items(self):
        return ['thabloid:index']

    def location(self, item):
        return reverse(item)


class ThabloidSitemap(sitemaps.Sitemap):
    changefreq = 'never'

    def items(self):
        return models.Thabloid.objects.all()

    def location(self, item):
        return item.get_absolute_url()


sitemap = {
    'thabloid-static': StaticViewSitemap,
    'thabloid-thabloids': ThabloidSitemap,
}
