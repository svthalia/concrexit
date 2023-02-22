import collections
import json

from django.db.transaction import non_atomic_requests
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from moneybird.webhooks.processing import process_webhook_payload

WEBHOOK_CACHE_CAPACITY = 100


class WebhookCache:
    def __init__(self):
        self.cache = collections.deque([], WEBHOOK_CACHE_CAPACITY)

    def add(self, key):
        return self.cache.append(key)

    def __contains__(self, item):
        return item in self.cache


webhook_cache = WebhookCache()


@csrf_exempt
@require_POST
@non_atomic_requests
def webhook_receive(request):
    idempotency_key = request.headers.get("Idempotency-Key")
    if idempotency_key in webhook_cache:
        return HttpResponse("Webhook already processed.", content_type="text/plain")

    payload = json.loads(request.body)
    process_webhook_payload(payload)

    webhook_cache.add(idempotency_key)

    return HttpResponse("Webhook processed.", content_type="text/plain")
