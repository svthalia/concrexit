"""General views for the website."""

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.views import LoginView
from django.contrib.auth.views import LogoutView as BaseLogoutView
from django.contrib.auth.views import PasswordResetView
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic import ListView, TemplateView
from django.views.generic.base import View

from django_ratelimit.decorators import ratelimit


class IndexView(TemplateView):
    template_name = "index.html"


@method_decorator(staff_member_required, "dispatch")
class TestCrashView(View):
    """Test view to intentionally crash to test the error handling."""

    def dispatch(self, request, *args, **kwargs) -> HttpResponse:
        if not request.user.is_superuser:
            return HttpResponseForbidden("This is not for you")
        raise Exception("Test exception")


class PagedView(ListView):
    """A ListView with automatic pagination."""

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        print(kwargs)
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

        querydict = self.request.GET.copy()

        if "page" in querydict:
            del querydict["page"]

        context.update(
            {
                "page_range": page_range,
                "base_url": f"{self.request.path}?{querydict.urlencode()}&"
                if querydict
                else f"{self.request.path}?",
            }
        )

        return context


class RateLimitedPasswordResetView(PasswordResetView):
    @method_decorator(ratelimit(key="ip", rate="5/h"))
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class RateLimitedLoginView(LoginView):
    @method_decorator(ratelimit(key="ip", rate="30/h"))
    @method_decorator(ratelimit(key="post:username", rate="30/h"))
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class LogoutView(BaseLogoutView):
    # Allow GET logout still (this was deprecated in Django 5.0).
    http_method_names = ["get", "head", "post", "options"]


def rate_limited_view(request, *args, **kwargs):
    return HttpResponse("You are rate limited", status=429)


def admin_unauthorized_view(request):
    if not request.member:
        url = "/user/login"
        args = request.META.get("QUERY_STRING", "")
        if args:
            url = f"{url}?{args}"
        return redirect(url)
    elif not request.member.is_staff and not request.member.is_superuser:
        raise PermissionDenied("You are not allowed to access the administration page.")
    else:
        return redirect(request.GET.get("next", "/"))
