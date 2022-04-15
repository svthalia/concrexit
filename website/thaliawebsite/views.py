"""General views for the website."""
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.mixins import AccessMixin
from django.contrib.auth.views import redirect_to_login
from django.http import (
    HttpResponseForbidden,
    HttpResponse,
)
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.views.generic.base import View
from webauth import user_is_webauth_verified


class IndexView(TemplateView):
    template_name = "index.html"


@method_decorator(staff_member_required, "dispatch")
class TestCrashView(View):
    """Test view to intentionally crash to test the error handling."""

    def dispatch(self, request, *args, **kwargs) -> HttpResponse:
        if not request.user.is_superuser:
            return HttpResponseForbidden("This is not for you")
        raise Exception("Test exception")


class TwoFactorAuthenticationRequiredMixin(AccessMixin):
    """Verify the user passed BOTH authentication factors (password and Web
    Authentication)."""
    login_url = settings.WEBAUTH_VERIFY_URL

    def dispatch(self, request, *args, **kwargs):
        if not user_is_webauth_verified(request) and request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(), self.login_url)
        return super().dispatch(request, *args, **kwargs)
