"""General views for the website."""

from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, HttpResponseForbidden
from django.utils.decorators import method_decorator
from django.views.generic import ListView, TemplateView
from django.views.generic.base import View


class IndexView(TemplateView):
    template_name = "index.html"


@method_decorator(staff_member_required, "dispatch")
class TestCrashView(View):
    """Test view to intentionally crash to test the error handling."""

    def dispatch(self, request, *args, **kwargs) -> HttpResponse:
        if not request.user.is_superuser:
            return HttpResponseForbidden("This is not for you")
        # Test exception so we don't care about it being too broad
        raise Exception("Test exception")  # pylint: disable=broad-exception-raised


class PagedView(ListView):
    """A ListView with automatic pagination."""

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        page = context["page_obj"].number
        paginator = context["paginator"]

        # Show the two pages before and after the current page
        page_range_start = max(1, page - 2)
        page_range_stop = min(page + 3, paginator.num_pages + 1)

        # Add extra pages if we show less than 5 pages
        page_range_start = min(page_range_start, page_range_stop - 5)
        page_range_start = max(1, page_range_start)

        # Add extra pages if we still show less than 5 pages
        page_range_stop = max(page_range_stop, page_range_start + 5)
        page_range_stop = min(page_range_stop, paginator.num_pages + 1)

        page_range = range(page_range_start, page_range_stop)

        context.update(
            {
                "page_range": page_range,
            }
        )

        return context
