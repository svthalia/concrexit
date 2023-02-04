from django.conf import settings
from django.db.models.signals import post_save, pre_delete, pre_save
from django.utils import timezone

from events.models import EventRegistration
from members.models import Member
from newsletters.signals import sent_newsletter
from utils.models.signals import suspendingreceiver

from .models import Category, FoodOrderReminderMessage, Message, NewAlbumMessage


@suspendingreceiver(
    post_save,
    sender="photos.Album",
    dispatch_uid="schedule_new_album_pushnotification",
)
def schedule_new_album_pushnotification(sender, instance, **kwargs):
    """Create, update or delete a scheduled message for the saved album if necessary."""
    message = getattr(instance, "new_album_notification", None)

    if instance.hidden:
        # Remove existing not-sent notification if there is one.
        if message is not None and not message.sent:
            message.delete()
    elif message is None or not message.sent:
        # Update existing notification or create new one.

        if message is None:
            message = NewAlbumMessage(album=instance)

        message.title = "New album uploaded"
        message.body = f"A new photo album '{instance.title}' has just been uploaded"
        message.url = f"{settings.BASE_URL}{instance.get_absolute_url()}"
        message.time = timezone.now() + timezone.timedelta(hours=1)
        message.category = Category.objects.get(key=Category.PHOTO)
        message.save()

        message.users.set(Member.current_members.all())


@suspendingreceiver(
    sent_newsletter,
    dispatch_uid="send_newsletter_pushnotification",
)
def send_newsletter_pushnotification(sender, newsletter, **kwargs):
    """Send a push notification for the sent newsletter."""
    message = Message.objects.create(
        title=newsletter.title,
        body="Tap to view",
        url=settings.BASE_URL + newsletter.get_absolute_url(),
        category=Category.objects.get(key=Category.NEWSLETTER),
    )
    message.users.set(Member.current_members.all())
    message.send()


@suspendingreceiver(
    post_save,
    sender="pizzas.FoodEvent",
    dispatch_uid="schedule_food_order_reminder_pushnotification",
)
def schedule_food_order_reminder_pushnotification(sender, instance, **kwargs):
    """Create, update or delete a scheduled message for the food event if necessary."""
    message = getattr(instance, "end_reminder", None)

    if not instance.send_notification:
        # Remove existing not-sent notification if there is one.
        if message is not None and not message.sent:
            message.delete()
    else:
        # Update existing notification or create new one.
        if message is None:
            message = FoodOrderReminderMessage(food_event=instance)

        message.title = f"{instance.event.title}: Order food"
        message.body = "You can order food for 10 more minutes"
        message.category = Category.objects.get(key=Category.PIZZA)
        message.time = instance.end - timezone.timedelta(minutes=10)
        message.save()

        if instance.event.registration_required:
            message.users.set(
                instance.event.registrations.filter(member__isnull=False)
                .select_related("member")
                .values_list("member", flat=True)
            )
        else:
            message.users.set(Member.current_members.all())


@suspendingreceiver(
    post_save,
    sender=EventRegistration,
    dispatch_uid="add_registered_member_to_food_order_reminder",
)
def add_registered_member_to_food_order_reminder(sender, instance, **kwargs):
    """Update members on food order reminder notification."""
    if not instance.event.has_food_event:
        return

    message = getattr(instance.event.food_event, "end_reminder", None)
    if message is not None and not message.sent and instance.member is not None:
        if instance.date_cancelled:
            message.users.remove(instance.member)
        else:
            message.users.add(instance.member)


@suspendingreceiver(
    pre_save,
    sender="pizzas.FoodOrder",
    dispatch_uid="remove_ordered_members_from_food_order_reminder",
)
def remove_ordered_members_from_food_order_reminder(sender, instance, **kwargs):
    """Remove members from the food order reminder when they create an order."""
    message = getattr(instance.food_event, "end_reminder", None)
    if not instance.pk and message is not None and not message.sent:
        message.users.remove(instance.member)


@suspendingreceiver(
    pre_delete,
    sender="pizzas.FoodOrder",
    dispatch_uid="add_member_to_food_order_reminder_on_order_deletion",
)
def add_member_to_food_order_reminder_on_order_deletion(sender, instance, **kwargs):
    """Re-add user to food order reminder on order deletion."""
    message = getattr(instance.food_event, "end_reminder", None)
    if message is not None and not message.sent:
        message.users.add(instance.member)
