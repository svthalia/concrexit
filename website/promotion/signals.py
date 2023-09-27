from promotion import emails
from promotion.models import updated_status
from utils.models.signals import suspendingreceiver


@suspendingreceiver(
    updated_status,
    dispatch_uid="send_status_update",
)
def send_status_update(sender, updated_request, **kwargs):
    print("Does it run?")
    emails.send_status_update(updated_request)
