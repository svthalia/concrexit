from django.conf import settings
from django.db.models.signals import post_save

from members.models import Member
from utils.models.signals import suspendingreceiver

from ..models import Category, Message


@suspendingreceiver(
    post_save,
    sender="thabloid.Thabloid",
    dispatch_uid="schedule_new_thabloid_pushnotification",
)
def send_thabloid_pushnotification(sender, instance, created: bool, **kwargs):
    if not created:
        return
    message = Message.objects.create(
        title=f"Thabloid {instance.year}, #{instance.issue}",
        body="Tap to view",
        url=settings.BASE_URL + instance.get_absolute_url(),
        category=Category.objects.get(key=Category.THABLOID),
    )
    message.users.set(Member.current_members.all())
    message.send()
