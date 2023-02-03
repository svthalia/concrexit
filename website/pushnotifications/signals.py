from django.conf import settings
from django.db.models.signals import post_save
from django.utils import timezone

from members.models import Member
from newsletters.models import Newsletter
from newsletters.signals import sent_newsletter
from photos.models import Album
from utils.models.signals import suspendingreceiver

from .models import Category, Message, NewAlbumMessage


@suspendingreceiver(
    post_save,
    sender=Album,
    dispatch_uid="schedule_new_album_pushnotification",
)
def schedule_new_album_pushnotification(sender, instance: Album, **kwargs):
    """Create, update or delete a scheduled message for the saved album if necessary."""
    message = (
        instance.new_album_notification
        if hasattr(instance, "new_album_notification")
        else None
    )

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
def send_newsletter_pushnotification(sender, newsletter: Newsletter, **kwargs):
    """Send a push notification for the sent newsletter."""
    message = Message.objects.create(
        title=newsletter.title,
        body="Tap to view",
        url=settings.BASE_URL + newsletter.get_absolute_url(),
        category=Category.objects.get(key=Category.NEWSLETTER),
    )
    message.users.set(Member.current_members.all())
    message.send()
