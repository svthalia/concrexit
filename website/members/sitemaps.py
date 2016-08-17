from django.contrib import sitemaps
from django.urls import reverse

from . import models


class StaticViewSitemap(sitemaps.Sitemap):
    priority = 0.5
    changefreq = 'daily'

    def items(self):
        return ['members:index']

    def location(self, item):
        return reverse(item)


class BecomeAMemberDocumentSitemap(sitemaps.Sitemap):
    priority = 0.1

    def items(self):
        return models.BecomeAMemberDocument.objects.all()

    def location(self, item):
        return reverse('members:become-a-member-document', args=(item.pk,))


sitemap = {
    'members-static': StaticViewSitemap,
    'members-become-documents': BecomeAMemberDocumentSitemap,
}
