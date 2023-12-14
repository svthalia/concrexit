from django.conf import settings
from django.db.models.signals import post_delete, post_save
from django.utils import timezone

from events.models import Event, EventRegistration
from events.signals import user_left_queue
from members.models import Member
from utils.models.signals import suspendingreceiver

from ..models import (
    Category,
    EventStartReminderMessage,
    Message,
    RegistrationReminderMessage,
)


@suspendingreceiver(
    post_save, sender=Event, dispatch_uid="schedule_event_start_reminder"
)
def schedule_event_start_reminder(sender, instance, **kwargs):
    """Create, update or delete a scheduled start reminder for the event if necessary."""
    message = getattr(instance, "start_reminder", None)

    if not instance.published:
        # Remove existing not-sent notification if the event isn't published.
        if message is not None and not message.sent:
            instance.start_reminder = None
            message.delete()
    else:
        reminder_time = instance.start - timezone.timedelta(hours=1)

        # Delete reminder if the event is changed so that the reminder time has now passed.
        if (
            message is not None
            and message.time != reminder_time
            and reminder_time < timezone.now()
        ):
            instance.start_reminder = None
            message.delete()
            return

        # Don't update if the message has already been sent or the reminder time has passed.
        if (message is not None and message.sent) or reminder_time < timezone.now():
            return

        if message is None:
            message = EventStartReminderMessage(event=instance)

        message.title = "Event"
        message.body = f"'{instance.title}' starts in 1 hour"
        message.url = f"{settings.BASE_URL}{instance.get_absolute_url()}"
        message.category = Category.objects.get(key=Category.EVENT)
        message.time = reminder_time
        message.save()

        if instance.registration_required:
            message.users.set([r.member for r in instance.participants if r.member])
        else:
            message.users.set(Member.current_members.all())


@suspendingreceiver(
    post_save, sender=Event, dispatch_uid="schedule_registration_reminder"
)
def schedule_registration_reminder(sender, instance, **kwargs):
    """Create, update or delete a registration reminder for the event if necessary."""
    message = getattr(instance, "registration_reminder", None)

    if not instance.published or not instance.registration_required:
        # Remove existing not-sent notification if the event
        # isn't published or registration isn't required.
        if message is not None and not message.sent:
            instance.registration_reminder = None
            message.delete()
    else:
        reminder_time = instance.registration_start - timezone.timedelta(hours=1)

        # Delete reminder if the event is changed so that the reminder time has now passed.
        if (
            message is not None
            and message.time != reminder_time
            and reminder_time < timezone.now()
        ):
            instance.registration_reminder = None
            message.delete()
            return

        # Don't update if the message has already been sent or the reminder time has passed.
        if (message is not None and message.sent) or reminder_time < timezone.now():
            return

        if message is None:
            message = RegistrationReminderMessage(event=instance)

        message.title = "Event registration"
        message.body = f"Registration for '{instance.title}' starts in 1 hour"
        message.url = f"{settings.BASE_URL}{instance.get_absolute_url()}"
        message.category = Category.objects.get(key=Category.EVENT)
        message.time = reminder_time
        message.save()

        message.users.set(Member.current_members.all())


@suspendingreceiver(
    post_save,
    sender=EventRegistration,
    dispatch_uid="update_event_start_reminder_users_on_registration_save",
)
def update_event_start_reminder_users_on_registration_save(sender, instance, **kwargs):
    """Add or remove the member from the event start reminder."""
    message = getattr(instance.event, "start_reminder", None)

    if message is None or message.sent:
        return

    if instance.member is not None:
        if instance.event.registration_required:
            if instance.date_cancelled:
                message.users.remove(instance.member)
            else:
                message.users.add(instance.member)


@suspendingreceiver(
    post_delete,
    sender=EventRegistration,
    dispatch_uid="update_event_start_reminder_users_on_registration_delete",
)
def update_event_start_reminder_users_on_registration_delete(
    sender, instance, **kwargs
):
    """Remove the member from the event start reminder if registration is required."""
    message = getattr(instance.event, "start_reminder", None)

    if message is None or message.sent:
        return

    if instance.member is not None:
        if instance.event.registration_required:
            message.users.remove(instance.member)


@suspendingreceiver(
    user_left_queue,
    dispatch_uid="send_queue_notification_when_user_left_queue",
)
def send_queue_notification(sender, event, user, **kwargs):
    """Send a notification when a registration is cancelled and a new user can participate."""
    message = Message.objects.create(
        title=event.title,
        body="Someone cancelled, so you can now participate!",
        url=settings.BASE_URL + event.get_absolute_url(),
        category=Category.objects.get(key=Category.EVENT),
    )
    message.users.set(user)
    message.send()
