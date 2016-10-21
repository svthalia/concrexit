import re
import json
import requests
from django.contrib.auth.models import User
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone

import events.models as events_models
import members.models as members_models


FIELD_DATA_TYPES = {
    '0': events_models.RegistrationInformationField.TEXT_FIELD,
    '1': events_models.RegistrationInformationField.INTEGER_FIELD,
    '2': events_models.RegistrationInformationField.BOOLEAN_FIELD,
}


def naive_to_aware(date_string):
    """Convert string of form '%Y-%m-%d %H:%M:%S'
    to timezone aware datetime object"""

    naive_datetime = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
    return timezone.get_current_timezone().localize(naive_datetime)


class Command(BaseCommand):
    help = 'Migrate the events from the old website.'

    def handle(self, *args, **options):

        if not settings.EVENTS_MIGRATION_KEY:
            raise ImproperlyConfigured('EVENTS_MIGRATION_KEY not specified')

        events_api_url = 'https://thalia.nu/events/api/?apikey={}'.format(
            settings.EVENTS_MIGRATION_KEY)

        print('[*]Getting events json data')
        try:

            response = requests.get(events_api_url,
                                    headers={'User-Agent': 'The Donald'})

        except requests.RequestException:
            print('[!]Could not get {}'.format(events_api_url))
            return

        try:
            data = response.json()
        except json.decoder.JSONDecodeError:
            print('[!]No json data found')
            return

        event_fields_translations = {

            # name in data : name in model
            'title': 'title',
            'description': 'description',
            'location': 'location',
            'start_date': 'start',
            'end_date': 'end',
            'member_price': 'price',
            'thalia_costs': 'cost',
            'begin_registration': 'registration_start',
            'end_registration': 'registration_end',
            'end_cancel': 'cancel_deadline',
            'registration_not_needed_message': 'no_registration_message',
        }

        activity_map = {}
        registration_map = {}
        information_field_map = {}

        print('[*]Parsing event data.')
        # Event
        for event_data in data['events']:

            new_event = events_models.Event(
                published=bool(int(event_data['public'])),
                max_participants=int(event_data['registration_limit']),
            )

            for concrete_field in event_fields_translations:

                django_field = event_fields_translations[concrete_field]

                concrete_data = event_data[concrete_field]

                # MultilingualField
                if django_field in (
                        'title', 'description', 'location',
                        'no_registration_message'):
                    for language_code in ('en', 'nl'):
                        django_multilingualfield = '{}_{}'.format(
                            django_field, language_code)

                        if not hasattr(new_event, django_multilingualfield):
                            print('[!]Could neither find {} nor {}'.format(
                                django_field, django_multilingualfield))
                            return

                        setattr(new_event, django_multilingualfield,
                                concrete_data)

                # DateTimeField
                elif concrete_data and django_field in (
                        'start', 'end', 'registration_start',
                        'registration_end',
                        'cancel_deadline'):

                    setattr(new_event, django_field,
                            naive_to_aware(concrete_data))

                # DecimalField
                elif django_field in ('price', 'cost'):

                    if re.match(r'[-+]?\d*\.?\d+$', concrete_data):
                        setattr(new_event, django_field, float(concrete_data))
                    else:
                        # TODO: is 0 the right value?
                        setattr(new_event, django_field, 0)

            new_event.save()
            activity_map[event_data['id']] = new_event.pk

        print('[*]Parsing registration field data.')
        # RegistrationInformationField
        for field_data in data['extra_fields']:
            new_registration_information_field = \
                events_models.RegistrationInformationField(

                    # TODO: UGLY AF
                    name_en=field_data['field_name'],
                    name_nl=field_data['field_name'],
                    description_en=field_data['field_explanation'],
                    description_nl=field_data['field_explanation'],

                    type=FIELD_DATA_TYPES[field_data['data_type']],
                    required=True,
                    event=events_models.Event.objects.get(
                        pk=activity_map[field_data['activity_id']]
                    ),
                )

            new_registration_information_field.save()

            information_field_map[field_data['field_id']] = \
                new_registration_information_field.pk

        print('[*]Parsing registration data.')
        # Registration
        for registration_data in data['registrations']:

            new_registration = events_models.Registration(

                name=registration_data['name'],
                date=naive_to_aware(registration_data['date']),
                paid=bool(registration_data['paid']),

                event=events_models.Event.objects.get(
                    pk=activity_map[registration_data['activity_id']]
                ),
            )

            username = registration_data['username']
            if registration_data['username'] and User.objects.filter(
                    username=username).exists():
                registration_user = User.objects.get(username=username)
                new_registration.member = members_models.Member.objects.get(
                    user=registration_user)

            cancelled_date = registration_data['canceled']
            if cancelled_date:
                new_registration.cancelled_date = naive_to_aware(
                    cancelled_date)

            new_registration.save()
            registration_map[registration_data['id']] = new_registration.pk

        print('[*]Parsing registration field info data.')
        # fields info
        for field_info_data in data['extra_info']:

            registration_field = events_models.RegistrationInformationField.\
                objects.get(
                    pk=information_field_map[field_info_data['field_id']]
                )

            parameters = {
                'registration': events_models.Registration.objects.get(
                    pk=registration_map[field_info_data['registration_id']]),
                'field': registration_field,
            }

            if registration_field.type == events_models.\
                    RegistrationInformationField.TEXT_FIELD:

                new_registration_information = events_models. \
                    TextRegistrationInformation(
                        value=field_info_data['value'],
                        **parameters
                    )

            elif registration_field.type == events_models.\
                    RegistrationInformationField.BOOLEAN_FIELD:

                value = False

                if value and bool(int(field_info_data['value'])):
                    value = True

                new_registration_information = \
                    events_models.BooleanRegistrationInformation(
                        value=value,
                        **parameters)

            # registration_field.type == INTEGER_FIELD:
            else:

                new_registration_information = \
                    events_models.IntegerRegistrationInformation(
                        value=field_info_data['value'] or 0,
                        **parameters)

            new_registration_information.save()
