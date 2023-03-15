from django.conf import settings

from members.models import Member
from newsletters.signals import sent_newsletter
from utils.models.signals import suspendingreceiver

from ..models import Category, Message


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
    message.users.set(
        Member.current_members.filter(profile__receive_newsletter=True).all()
    )
    message.send()
