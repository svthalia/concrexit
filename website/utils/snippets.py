"""Provides various utilities that are useful across the project."""
import datetime
import hmac
from base64 import urlsafe_b64decode, urlsafe_b64encode
from collections import namedtuple
from hashlib import sha1

from django.conf import settings
from django.contrib.admin.models import LogEntry
from django.core.mail import EmailMultiAlternatives
from django.template import loader
from django.template.defaultfilters import urlencode
from django.templatetags.static import static
from django.utils import dateparse, timezone

from rest_framework.exceptions import ParseError


def dict2obj(d, name="Object"):
    return namedtuple(name, d.keys())(*d.values())


def strtobool(val):
    """Convert a string representation of truth to true (1) or false (0).

    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
    'val' is anything else.
    """
    val = val.lower()
    if val in ("y", "yes", "t", "true", "on", "1"):
        return 1
    if val in ("n", "no", "f", "false", "off", "0"):
        return 0
    raise ValueError(f"invalid truth value {val}")


def datetime_to_lectureyear(date):
    """Convert a :class:`~datetime.date` to the start of the lectureyear.

    >>> from datetime import date, datetime, timezone
    >>> nov_23 = date(1990, 11, 7)
    >>> datetime_to_lectureyear(nov_23)
    1990
    >>> mar_2 = date(1993, 3, 2)
    >>> datetime_to_lectureyear(mar_2)
    1992

    Also works on :class:`~datetime.datetime`, but they need to be tz-aware:

    >>> new_year = datetime(2000, 1, 1, tzinfo=timezone.utc)
    >>> datetime_to_lectureyear(new_year)
    1999
    """
    if isinstance(date, timezone.datetime):
        date = timezone.localtime(date).date()
    sept_1 = timezone.make_aware(timezone.datetime(date.year, 9, 1))
    if date < sept_1.date():
        return date.year - 1
    return date.year


def create_google_maps_url(location, zoom, size):
    """Return a Google Maps URL for a given location.

    The URL can be relative if it's a static file, so you may need to use
    request.build_absolute_uri() to get the full URL suitable for an API.
    """
    if location.lower().strip() == "online":
        return static("img/locations/online.png")
    if location.lower().strip() == "discord":
        return static("img/locations/discord.png")

    maps_url = (
        f"/maps/api/staticmap?"
        f"center={ urlencode(location) }&"
        f"zoom={ zoom }&size={ size }&"
        f"markers={ urlencode(location) }&"
        f"key={ settings.GOOGLE_MAPS_API_KEY }"
    )

    decoded_key = urlsafe_b64decode(settings.GOOGLE_MAPS_API_SECRET)

    signature = hmac.new(decoded_key, maps_url.encode(), sha1)

    encoded_signature = urlsafe_b64encode(signature.digest())

    maps_url += f"&signature={encoded_signature.decode('utf-8')}"

    return "https://maps.googleapis.com" + maps_url


def _extract_date(param):
    """Extract the date from an arbitrary string."""
    if param is None:
        return None
    try:
        return dateparse.parse_datetime(param)
    except ValueError:
        return dateparse.parse_date(param)


def extract_date_range(request, allow_empty=False):
    """Extract a date range from an arbitrary string."""
    default_value = None

    start = request.query_params.get("start", default_value)
    if start or not allow_empty:
        try:
            start = dateparse.parse_datetime(start)
            if not timezone.is_aware(start):
                start = timezone.make_aware(start)
        except (ValueError, AttributeError, TypeError) as e:
            raise ParseError(detail="start query parameter invalid") from e

    end = request.query_params.get("end", default_value)
    if end or not allow_empty:
        try:
            end = dateparse.parse_datetime(end)
            if not timezone.is_aware(end):
                end = timezone.make_aware(end)
        except (ValueError, AttributeError, TypeError) as e:
            raise ParseError(detail="end query parameter invalid") from e

    return start, end


def overlaps(check, others, can_equal=True):
    """Check for overlapping date ranges.

    This works by checking the maximum of the two `since` times, and the minimum of
    the two `until` times. Because there are no infinite dates, the value date_max
    is created for when the `until` value is None; this signifies a timespan that
    has not ended yet and is the maximum possible date in Python's datetime.

    The ranges overlap when the maximum start time is smaller than the minimum
    end time, as can be seen in this example of two integer ranges:

    check: . . . .[4]. . . . 9
    other: . . 2 . .[5]. . . .

    check: . . . .[4]. . . . 9
    other: . . 2 . . . . . . . [date_max]

    And when non overlapping:
    check: . . . . . .[6] . . 9
    other: . . 2 . .[5]. . . .

    4 < 5 == True so these intervals overlap, while 6 < 5 == False so these intervals
    don't overlap

    The can_equal argument is used for boards, where the end date can't be the same
    as the start date.

    >>> overlaps( \
    dict2obj({ \
        'pk': 1 \
        , 'since': datetime.date(2018, 12, 1) \
        , 'until': datetime.date(2019, 1, 1) \
    }) \
    , [dict2obj({ \
    'pk': 2 \
    , 'since': datetime.date(2019, 1, 1) \
    , 'until': datetime.date(2019, 1, 31) \
    })])
    False

    >>> overlaps( \
    dict2obj({ \
        'pk': 1 \
        , 'since': datetime.date(2018, 12, 1) \
        , 'until': datetime.date(2019, 1, 1) \
    }) \
    , [dict2obj({ \
    'pk': 2 \
    , 'since': datetime.date(2019, 1, 1) \
    , 'until': datetime.date(2019, 1, 31) \
    })], False)
    True

    >>> overlaps( \
    dict2obj({ \
        'pk': 1 \
        , 'since': datetime.date(2018, 12, 1) \
        , 'until': datetime.date(2019, 1, 2) \
    }) \
    , [dict2obj({ \
    'pk': 2 \
    , 'since': datetime.date(2019, 1, 1) \
    , 'until': datetime.date(2019, 1, 31) \
    })])
    True
    """
    date_max = datetime.date(datetime.MAXYEAR, 12, 31)
    for other in others:
        if check.pk == other.pk:
            # No checks for the object we're validating
            continue

        max_start = max(check.since, other.since)
        min_end = min(check.until or date_max, other.until or date_max)

        if max_start == min_end and not can_equal:
            return True
        if max_start < min_end:
            return True

    return False


def send_email(
    to: list[str],
    subject: str,
    txt_template: str,
    context: dict,
    html_template: str | None = None,
    bcc: list[str] | None = None,
    from_email: str | None = None,
    connection=None,
) -> None:
    txt_message = loader.render_to_string(txt_template, context)

    mail = EmailMultiAlternatives(
        subject=f"[THALIA] {subject}",
        body=txt_message,
        to=to,
        bcc=bcc,
        from_email=from_email,
        connection=connection,
    )

    if html_template is not None:
        html_message = loader.render_to_string(html_template, context)
        mail.attach_alternative(html_message, "text/html")

    mail.send()


def minimise_logentries_data(dry_run=False):
    # Sometimes years are 366 days of course, but better delete 1 or 2 days early than late
    deletion_period = timezone.now().date() - timezone.timedelta(days=365 * 7)

    queryset = LogEntry.objects.filter(action_time__lte=deletion_period).exclude(
        user__isnull=True
    )
    if not dry_run:
        queryset.update(user=None)
    return queryset
