from celery import shared_task
from django.apps import apps


@shared_task
def send_message(message_id):
    """Send a push notification"""

    print('Sending push notification {}'.format(message_id))

    ScheduledMessage = apps.get_model('pushnotifications', 'ScheduledMessage')
    try:
        message = ScheduledMessage.objects.get(pk=message_id)
    except ScheduledMessage.DoesNotExist:
        print('Cannot find ScheduledMessage')
        return

    message.send()
