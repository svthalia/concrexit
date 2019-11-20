import os

from django.conf import settings
from django.template.loader import get_template
from django.utils import translation, timezone

from events.models import Event
from newsletters import emails
from partners.models import Partner
from pushnotifications.models import Message, Category


def write_to_file(pk, lang, html_message):
    """
    Write newsletter to a file
    """
    cache_dir = os.path.join(settings.MEDIA_ROOT, "newsletters")
    if not os.path.isdir(cache_dir):
        os.makedirs(cache_dir)

    with open(os.path.join(cache_dir, f"{pk}_{lang}.html"), "w+") as cache_file:
        cache_file.write(html_message)


def save_to_disk(newsletter, request):
    """
    Writes the newsletter as HTML to file (in all languages)
    """
    main_partner = Partner.objects.filter(is_main_partner=True).first()
    local_partner = Partner.objects.filter(is_local_partner=True).first()

    html_template = get_template("newsletters/email.html")

    for language in settings.LANGUAGES:
        translation.activate(language[0])

        context = {
            "newsletter": newsletter,
            "agenda_events": (
                newsletter.newslettercontent_set.filter(newsletteritem=None).order_by(
                    "newsletterevent__start_datetime"
                )
            ),
            "main_partner": main_partner,
            "local_partner": local_partner,
            "lang_code": language[0],
            "request": request,
        }

        html_message = html_template.render(context)

        write_to_file(newsletter.pk, language[0], html_message)


def get_agenda(start_date):
    end_date = start_date + timezone.timedelta(weeks=2)
    base_events = Event.objects.filter(
        start__gte=start_date, end__lt=end_date, published=True
    ).order_by("start")
    if base_events.count() < 10:
        more_events = Event.objects.filter(end__gte=end_date).order_by("start")
        return [*base_events, *more_events][:10]
    return base_events


def send_newsletter(newsletter):
    emails.send_newsletter(newsletter)
    newsletter.sent = True
    newsletter.save
    Message.objects.create(
        title_nl = newsletter.title_nl,
        title_en = newsletter.title_en,
        users = newsletter.users,
        body_nl = newsletter.description_nl,
        body_en = newsletter.description_en,
        url = settings.BASE_URL + newsletter.get_absolute_url(),
        category = Category.objects.get(
key="newsletter"
        )
    ).send()
