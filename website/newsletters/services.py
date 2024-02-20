import base64
import logging
from io import BytesIO

from django.core.files.base import ContentFile
from django.template.loader import get_template
from django.utils import timezone

import requests
from bs4 import BeautifulSoup
from PIL import Image

from events.models import Event
from newsletters import emails
from partners.models import Partner

from .signals import sent_newsletter

logger = logging.getLogger(__name__)


def save_to_disk(newsletter):
    """Write the newsletter as HTML to file (in all languages)."""
    main_partner = Partner.objects.filter(is_main_partner=True).first()
    local_partners = split_local_partners()

    html_template = get_template("newsletters/email.html")

    context = {
        "newsletter": newsletter,
        "agenda_events": (
            newsletter.newslettercontent_set.filter(newsletteritem=None).order_by(
                "newsletterevent__start_datetime"
            )
        ),
        "main_partner": main_partner,
        "local_partners": local_partners,
    }

    html_message = html_template.render(context)
    html_message = embed_linked_html_images(html_message)

    newsletter.rendered_file = ContentFile(html_message.encode("utf-8"))
    newsletter.save()


def embed_linked_html_images(html_input):
    bs = BeautifulSoup(html_input, "html.parser")

    output = html_input
    images = bs.findAll("img")

    for image in images:
        source = image["src"]
        if not "source".startswith(("http://", "https://")):
            continue
        try:
            response = requests.get(source, timeout=30.0)
            image = Image.open(BytesIO(response.content))
            buffer = BytesIO()
            image.save(buffer, format="png")
            base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
            encoded_image = "data:image/png;base64," + base64_image
            output = output.replace(source, encoded_image)
        except OSError:
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

    sent_newsletter.send(sender=None, newsletter=newsletter)

    save_to_disk(newsletter)


def split_local_partners():
    all_local_partners = Partner.objects.filter(
        is_local_partner=True, is_active=True
    ).order_by("?")
    local_partner_count = len(all_local_partners)
    local_partners = []
    for i in range(local_partner_count // 2):
        local_partners.append(
            [all_local_partners[i * 2], all_local_partners[i * 2 + 1]]
        )

    if local_partner_count % 2 != 0:
        local_partners.append([all_local_partners[local_partner_count - 1]])

    return local_partners
