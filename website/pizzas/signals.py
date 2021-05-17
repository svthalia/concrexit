"""The signals checked by the pizzas package."""
from django.db.models.signals import post_save, pre_delete, pre_save

from utils.models.signals import suspendingreceiver


@suspendingreceiver(
    post_save,
    sender="events.EventRegistration",
    dispatch_uid="pizzas_registration_save",
)
def post_registration_save(sender, instance, **kwargs):
    """Update members on pizza reminder notification."""
    event = instance.event
    if (
        event.has_food_event
        and event.pizzaevent.send_notification
        and instance.member is not None
    ):
        if instance.date_cancelled:
            event.pizzaevent.end_reminder.users.remove(instance.member)
        else:
            event.pizzaevent.end_reminder.users.add(instance.member)


@suspendingreceiver(
    pre_save, sender="pizzas.FoodOrder", dispatch_uid="food_foodorder_save"
)
def pre_order_save(sender, instance, **kwargs):
    """Remove user from the order reminder when saved."""
    if (
        not instance.pk
        and instance.food_event.end_reminder
        and not instance.food_event.end_reminder.sent
    ):
        instance.food_event.end_reminder.users.remove(instance.member)


@suspendingreceiver(
    pre_delete, sender="pizzas.FoodOrder", dispatch_uid="food_foodorder_delete"
)
def pre_order_delete(sender, instance, **kwargs):
    """Re-add user to reminder to on order deletion."""
    if instance.food_event.end_reminder and not instance.food_event.end_reminder.sent:
        instance.food_event.end_reminder.users.add(instance.member)
