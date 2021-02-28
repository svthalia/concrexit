from django.http import HttpResponseRedirect
from django.views.generic.detail import DetailView

from .models import ShortLink


class ShortLinkView(DetailView):
    model = ShortLink
    context_object_name = "link"
    template_name = "shortlinks/confirm.html"

    def render_to_response(self, context, **kwargs):
        if self.object.immediate:
            return HttpResponseRedirect(self.object.url)
        return super().render_to_response(context, **kwargs)
