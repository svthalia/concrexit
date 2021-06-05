from django.contrib.admin import ModelAdmin
from django.core.exceptions import DisallowedRedirect
from django.http import HttpResponseRedirect
from django.utils.http import url_has_allowed_host_and_scheme


def _do_next(request, response):
    """See DoNextModelAdmin."""
    if "next" in request.GET:
        if not url_has_allowed_host_and_scheme(
            request.GET["next"], allowed_hosts={request.get_host()}
        ):
            raise DisallowedRedirect
        if "_save" in request.POST:
            return HttpResponseRedirect(request.GET["next"])
        if response is not None:
            return HttpResponseRedirect(
                "{}?{}".format(response.url, request.GET.urlencode())
            )
    return response


class DoNextModelAdmin(ModelAdmin):
    """This class adds processing of a `next` parameter in the urls of the add and change admin forms.

    If it is set and safe this override will redirect the user to the provided url.
    """

    def response_add(self, request, obj, **kwargs):
        res = super().response_add(request, obj, **kwargs)
        return _do_next(request, res)

    def response_change(self, request, obj):
        res = super().response_change(request, obj)
        return _do_next(request, res)
