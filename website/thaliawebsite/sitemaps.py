from django.contrib import sitemaps
from django.urls import reverse


class StaticViewSitemap(sitemaps.Sitemap):

    def items(self):
        return ['index', 'become-active', 'sister-associations',
                'become-a-member', 'contact']

    def location(self, item):
        return reverse(item)
