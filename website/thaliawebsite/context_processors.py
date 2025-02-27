from django.conf import settings
from django.utils import timezone


def source_commit(_):
    """Get the SOURCE_COMMIT environment variable."""
    return {"SOURCE_COMMIT": settings.SOURCE_COMMIT}


def aprilfools(_):
    now = timezone.now()
    return {"APRIL_FOOLS": now.month == 4 and now.day == 1}


def lustrum_styling(_):
    return {
        "lustrumstyling": timezone.datetime(2022, 4, 22).date()
        <= timezone.now().date()
        <= timezone.datetime(2022, 4, 29).date()
    }


def year_as_hex(_):
    now = timezone.now().year
    return {"YEAR_IN_HEX": hex(now)}
