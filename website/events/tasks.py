from celery import shared_task

from events.emails import notify_registration
from events.models import EventRegistration


@shared_task
def send_registration_confirmation_email(registration_id: int):
    try:
        registration = EventRegistration.objects.get(pk=registration_id)
    except EventRegistration.DoesNotExist:
        return  # The registration was deleted.
    if (
        # Repeat the checks from the calling signal just in case
        # something changed between calling and running this task.
        registration.is_registered
        and registration.email
        and registration.event.registration_required
        and (
            registration.member is None
            or registration.member.profile.receive_registration_confirmation
        )
    ):
        notify_registration(registration)
