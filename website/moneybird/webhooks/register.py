import logging

from django.urls import reverse

from moneybird.administration import get_moneybird_administration
from moneybird.settings import settings


def get_webhook_receive_endpoint():
    if not settings.MONEYBIRD_WEBHOOK_SITE_DOMAIN:
        return None
    return settings.MONEYBIRD_WEBHOOK_SITE_DOMAIN + reverse("moneybird:webhook_receive")


def create_webhook():
    if settings.MONEYBIRD_WEBHOOK_SITE_DOMAIN.startswith("http://") and not (
        settings.DEBUG or settings.MONEYBIRD_WEBHOOK_ALLOW_INSECURE
    ):
        logging.warning("MONEYBIRD_WEBHOOK_SITE_DOMAIN is not secure")
        return None

    url = get_webhook_receive_endpoint()
    if not url:
        return

    events = settings.MONEYBIRD_WEBHOOK_EVENTS
    if events is None:
        logging.info("No events to register a webhook for.")
        return

    events = [event.value for event in events]

    administration = get_moneybird_administration()
    response = administration.post("webhooks", data={"url": url, "events": events})
    logging.info(f"Registered webhook with id {response['id']}")
    return response


def get_webhooks():
    administration = get_moneybird_administration()
    return administration.get("webhooks")


def delete_webhook(webhook_id):
    administration = get_moneybird_administration()
    response = administration.delete(f"webhooks/{webhook_id}")
    logging.info(f"Unregistered webhook with id {webhook_id}")
    return response
