import logging

from moneybird.resource_types import (
    MoneybirdResource,
    get_moneybird_resource_type_for_entity,
)
from moneybird.settings import settings
from moneybird.webhooks.events import WebhookEvent


def process_webhook_payload(payload: MoneybirdResource) -> None:
    if payload["action"] == "test_webhook":
        logging.info(f"Received test webhook from Moneybird: {payload}")
        return

    if payload["webhook_id"] != settings.MONEYBIRD_WEBHOOK_ID:
        logging.error("Received webhook with wrong id")
        return

    if payload["webhook_token"] != settings.MONEYBIRD_WEBHOOK_TOKEN:
        logging.error("Received webhook with wrong token")
        return

    if int(payload["administration_id"]) != settings.MONEYBIRD_ADMINISTRATION_ID:
        logging.error("Received webhook for wrong administration")
        return

    try:
        event = WebhookEvent(payload["action"])
    except ValueError:
        logging.error("Received webhook with invalid event")
        return

    entity_type = payload["entity_type"]
    entity_id = payload["entity_id"]
    entity_data = payload["entity"]
    resource_type = get_moneybird_resource_type_for_entity(entity_type)

    if resource_type is None:
        logging.warning("Received webhook with unregistered entity type")
        return

    return resource_type.process_webhook_event(entity_id, entity_data, event)
