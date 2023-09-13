from django.db.models.signals import post_save

from events.models import EventRegistration
from events.tasks import send_registration_confirmation_email
from utils.models.signals import suspendingreceiver


@suspendingreceiver(
    post_save,
    sender=EventRegistration,
    dispatch_uid="send_event_registration_confirmation",
)
def send_event_registration_confirmation(
    sender, instance: EventRegistration, created: bool, **kwargs
):
    """Send an email notifying the registered person that they are registered."""
    if (
        created
        and instance.is_registered
        and instance.email
        and instance.event.registration_required
        and (  # Don't send email to users who don't want it.
            instance.member is None
            or instance.member.profile.receive_registration_confirmation
        )
    ):
        # Start a celery task to email the user in the background.
        send_registration_confirmation_email.apply_async((instance.pk,), expires=600)
