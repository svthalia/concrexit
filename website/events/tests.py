import datetime

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from events.models import Event, Registration
from members.models import Member


class RegistrationTest(TestCase):
    """Tests event registrations"""

    fixtures = ['members.json']

    def setUp(self):
        self.event = Event.objects.create(
            title_nl='testevene',
            title_en='testevent',
            description_en='desc',
            description_nl='besch',
            start=timezone.now(),
            end=(timezone.now() + datetime.timedelta(hours=1)),
            location_en='test location',
            location_nl='test locatie',
            map_location='test map location',
            price=0.00,
            fine=0.00)
        self.member = Member.objects.all()[0]

    def test_registration_either_name_or_member(self):
        r1 = Registration.objects.create(event=self.event, member=self.member)
        r1.clean()
        r2 = Registration.objects.create(event=self.event, name='test name')
        r2.clean()
        with self.assertRaises(ValidationError):
            r3 = Registration.objects.create(event=self.event,
                                             name='test name',
                                             member=self.member)
            r3.clean()
