"""Tests for the pizza functionality"""
import datetime

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone, translation

from freezegun import freeze_time

from activemembers.models import Committee
from events.models import Event
from pizzas.models import PizzaEvent


@freeze_time('2018-03-21')
class PizzaEventTestCase(TestCase):
    """Test the pizzaevent class"""
    fixtures = ['members.json', 'committees.json']

    @classmethod
    def setUpTestData(cls):
        cls.committee = Committee.objects.get(pk=1)
        cls.event = Event.objects.create(
            title_nl="testevent nl",
            title_en="testevent en",
            description_en='desc',
            description_nl='besch',
            start=(timezone.now() + datetime.timedelta(hours=1)),
            end=(timezone.now() + datetime.timedelta(hours=2)),
            organiser=cls.committee,
            location_en='test location',
            location_nl='test locatie',
            map_location='test map location',
            price=0.00,
            fine=5.00)

        cls.event2 = Event.objects.create(
            title_nl="testevent2 nl",
            title_en="testevent2 en",
            description_en='desc2',
            description_nl='besch2',
            start=(timezone.now() + datetime.timedelta(hours=4)),
            end=(timezone.now() + datetime.timedelta(hours=8)),
            organiser=cls.committee,
            location_en='test location2',
            location_nl='test locatie2',
            map_location='test map location',
            price=0.00,
            fine=5.00)

        cls.pizzaEvent = PizzaEvent.objects.create(
            event=cls.event,
            start=timezone.now() - datetime.timedelta(hours=1),
            end=timezone.now() + datetime.timedelta(hours=2),
        )

    def test_title(self):
        """Check the title attribute"""
        for lang in ['en', 'nl']:
            with self.subTest(lang=lang):
                translation.activate(lang)
                self.assertEqual(self.pizzaEvent.title, self.event.title)

    def test_current(self):
        """Test the classmethod that fetches a currently active pizzaevent"""
        with self.subTest(msg="Single event, active"):
            self.assertEqual(self.pizzaEvent, PizzaEvent.current())

        with self.subTest(mgs="Single event, not active"):
            self.pizzaEvent.start = (
                timezone.now() + datetime.timedelta(hours=10))
            self.pizzaEvent.end = (
                timezone.now() + datetime.timedelta(hours=100))
            self.pizzaEvent.save()
            self.assertIsNone(PizzaEvent.current())

        second_pizzaevent = PizzaEvent.objects.create(
            start=timezone.now() + datetime.timedelta(hours=100),
            end=timezone.now() + datetime.timedelta(hours=1000),
            event=self.event2)

        with self.subTest(msg="two events, not active"):
            self.assertIsNone(PizzaEvent.current())

        self.pizzaEvent.start = timezone.now() - datetime.timedelta(hours=1)
        self.pizzaEvent.end = (timezone.now() + datetime.timedelta(hours=1))
        self.pizzaEvent.save()

        with self.subTest(msg="two events, one active"):
            self.assertEqual(self.pizzaEvent, PizzaEvent.current())

        second_pizzaevent.start = timezone.now() + datetime.timedelta(hours=2)
        second_pizzaevent.save()
        with self.subTest(msg="two events, within 8 hours"):
            self.assertEqual(self.pizzaEvent, PizzaEvent.current())

        self.pizzaEvent.end = timezone.now() - datetime.timedelta(minutes=10)
        self.pizzaEvent.save()
        with self.subTest(msg="two events, within 8 hours, first ended"):
            self.assertEqual(second_pizzaevent, PizzaEvent.current())

    def test_clean(self):
        """Check if clean method works"""
        new = PizzaEvent(
            event=self.event2,
            start=self.pizzaEvent.start + datetime.timedelta(minutes=10),
            end=timezone.now() + datetime.timedelta(hours=100),
        )
        with self.subTest(msg="overlapping event"):
            with self.assertRaises(ValidationError):
                new.clean()

        new.end = timezone.now() - datetime.timedelta(hours=100)
        with self.subTest(msg="end before start"):
            with self.assertRaises(ValidationError):
                new.clean()
