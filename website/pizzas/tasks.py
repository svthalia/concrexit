from __future__ import absolute_import

from celery import shared_task
from django.apps import apps
from django.utils import timezone


@shared_task
def create_send_message(pizza_id):
    """Send a push notification"""

    print('Sending push notification for pizza event {}'.format(pizza_id))

    PizzaEvent = apps.get_model('pizzas', 'PizzaEvent')
    try:
        pizza_event = PizzaEvent.objects.get(pk=pizza_id)
    except PizzaEvent.DoesNotExist:
        print('Cannot find pizza event')
        return

    Message = apps.get_model('pushnotifications', 'Message')
    Category = apps.get_model('pushnotifications', 'Category')
    Member = apps.get_model('members', 'Member')

    end_reminder = Message()
    end_reminder.title_en = 'Order pizza'
    end_reminder.title_nl = 'Pizza bestellen'
    end_reminder.body_en = 'You can order pizzas for 10 more minutes'
    end_reminder.body_nl = "Je kan nog 10 minuten pizza's bestellen"
    end_reminder.category = Category.objects.get(key='pizza')
    end_reminder.save()

    if pizza_event.event.registration_required:
        pizza_event.end_reminder.users.set(
            pizza_event.event.registration_set.filter(
                date_cancelled__isnull=True
            )
        )
    else:
        pizza_event.end_reminder.users.set(Member.active_members.all())

    pizza_event.save()

    end_reminder.send()
