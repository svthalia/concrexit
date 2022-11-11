"""General views for the website."""

from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, HttpResponseForbidden
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.views.generic.base import View


class IndexView(TemplateView):
    template_name = "index.html"


@method_decorator(staff_member_required, "dispatch")
class TestCrashView(View):
    """Test view to intentionally crash to test the error handling."""

    def dispatch(self, request, *args, **kwargs) -> HttpResponse:
        if not request.user.is_superuser:
            return HttpResponseForbidden("This is not for you")
        raise Exception("Test exception")
