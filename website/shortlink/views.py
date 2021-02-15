from django.http import Http404, HttpResponseRedirect
from django.views.generic import TemplateView

from shortlink.models import ShortLink


class ShortLinkView(TemplateView):
    template_name = "shortlink.html"

    def dispatch(self, request, *args, **kwargs):
        self.link = ShortLink.objects.filter(key=kwargs["slug"]).first()
        if self.link is None:
            raise Http404()
        if self.link.immediate:
            return HttpResponseRedirect(self.link.url)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["link_key"] = self.link.key
        context["link_url"] = self.link.url
        return context
