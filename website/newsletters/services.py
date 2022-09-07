import base64
import logging
import math
import os
from io import BytesIO

import requests
from PIL import Image
from bs4 import BeautifulSoup
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import DefaultStorage
from django.template.loader import get_template
from django.utils import translation, timezone

from events.models import Event
from members.models import Member
from newsletters import emails
from partners.models import Partner
from pushnotifications.models import Message, Category

logger = logging.getLogger(__name__)


def write_to_file(pk, lang, html_message):
    """Write newsletter to a file."""
    storage = DefaultStorage()

    cache_dir = "newsletters"
    file_path = os.path.join(cache_dir, f"{pk}_{lang}.html")
    storage.save(file_path, ContentFile(html_message))


def save_to_disk(newsletter):
    """Write the newsletter as HTML to file (in all languages)."""
    main_partner = Partner.objects.filter(is_main_partner=True).first()
    all_local_partners = Partner.objects.filter(is_local_partner=True).order_by("?")
    local_partner_count = len(all_local_partners)
    local_partners = []
    for i in range(math.floor(local_partner_count/2)):
        local_partners.append([all_local_partners[i*2], all_local_partners[i*2 + 1]])

    if local_partner_count % 2 != 0:
        local_partners.append([all_local_partners[local_partner_count-1]])

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
            "local_partners": local_partners,
            "lang_code": language[0],
        }

        html_message = html_template.render(context)
        html_message = embed_linked_html_images(html_message)

        write_to_file(newsletter.pk, language[0], html_message)


def embed_linked_html_images(html_input):
    bs = BeautifulSoup(html_input, "html.parser")

    output = html_input
    images = bs.findAll("img")

    for image in images:
        try:
            source = image["src"]
            response = requests.get(source)
            image = Image.open(BytesIO(response.content))
            buffer = BytesIO()
            image.save(buffer, format="png")
            base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
            encoded_image = "data:image/png;base64, " + base64_image
            output = output.replace(source, encoded_image)
        except IOError:
            logger.warning(f"Image could not be found: {image}")

    return output


def get_agenda(start_date):
    end_date = start_date + timezone.timedelta(weeks=2)
    published_events = Event.objects.filter(published=True)
    base_events = published_events.filter(
        start__gte=start_date, end__lt=end_date
    ).order_by("start")
    if base_events.count() < 10:
        more_events = published_events.filter(end__gte=end_date).order_by("start")
        return [*base_events, *more_events][:10]
    return base_events


def send_newsletter(newsletter):
    emails.send_newsletter(newsletter)
    newsletter.sent = True
    newsletter.save()
    message = Message.objects.create(
        title=newsletter.title,
        body="Tap to view",
        url=settings.BASE_URL + newsletter.get_absolute_url(),
        category=Category.objects.get(key=Category.NEWSLETTER),
    )
    message.users.set(Member.current_members.all())
    message.send()

    save_to_disk(newsletter)
