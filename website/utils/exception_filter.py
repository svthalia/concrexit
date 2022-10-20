"""Provides an exception filter for django."""
import logging

from django.views.debug import SafeExceptionReporterFilter

__LOGGER = logging.getLogger(__name__)


class ThaliaSafeExceptionReporterFilter(SafeExceptionReporterFilter):
    """Filter additional variables from tracebacks.

    https://docs.djangoproject.com/en/2.0/howto/error-reporting/#filtering-sensitive-information
    """

    def get_traceback_frame_variables(self, request, tb_frame):
        """Filter traceback frame variables."""
        local_vars = super().get_traceback_frame_variables(request, tb_frame)

        if self.is_active(request):
            for name, val in local_vars:
                if name == "request":
                    try:
                        val.COOKIES = {"cookies have been cleaned": True}
                        val.META[
                            "HTTP_COOKIE"
                        ] = SafeExceptionReporterFilter.cleansed_substitute
                        val.META[
                            "HTTP_AUTHORIZATION"
                        ] = SafeExceptionReporterFilter.cleansed_substitute
                    except (AttributeError, IndexError):
                        __LOGGER.exception("Somehow cleaning the request failed")

        return local_vars
