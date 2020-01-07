"""The signals checked by the pizzas package"""
from django.db.models.signals import post_save

from utils.models.signals import suspendingreceiver


@suspendingreceiver(
    post_save, sender="events.Registration", dispatch_uid="pizzas_registration_save"
)
def post_registration_save(sender, instance, **kwargs):
    """Update members on pizza reminder notification"""
    event = instance.event
    if (
        event.is_pizza_event()
        and event.pizzaevent.send_notification
        and instance.member is not None
    ):
        if instance.date_cancelled:
            event.pizzaevent.end_reminder.users.remove(instance.member)
        else:
            event.pizzaevent.end_reminder.users.add(instance.member)
