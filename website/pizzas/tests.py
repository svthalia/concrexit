"""Tests for the pizza functionality"""
import datetime

from django.contrib.auth.models import Permission, ContentType
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone, translation

from freezegun import freeze_time

from activemembers.models import Committee
from members.models import Member
from events.models import Event
from pizzas.models import PizzaEvent, Order
from pizzas import services


@freeze_time('2018-03-21')
@override_settings(SUSPEND_SIGNALS=True)
class PizzaEventTestCase(TestCase):
    """Test the pizzaevent class"""
    fixtures = ['members.json', 'member_groups.json']

    @classmethod
    def setUpTestData(cls):
        # set up user with change_order perm
        cls.member = Member.objects.get(pk=3)  # a non-superuser
        content_type = ContentType.objects.get_for_model(Order)
        cls.change_order_perm = Permission.objects.get(
            codename='change_order',
            content_type=content_type)
        cls.member.user_permissions.add(cls.change_order_perm)

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

    def test_validate_unique(self):
        """Check if uniqueness validation is correct"""
        self.pizzaEvent.start = self.pizzaEvent.start + datetime.timedelta(
            minutes=10)

        with self.subTest(msg="saving works"):
            self.pizzaEvent.validate_unique()

        new = PizzaEvent(
            event=self.event2,
            start=self.pizzaEvent.start + datetime.timedelta(minutes=10),
            end=timezone.now() + datetime.timedelta(hours=100),
        )
        with self.subTest(msg="overlapping event"):
            with self.assertRaises(ValidationError):
                new.validate_unique()

    def test_clean(self):
        """Check if clean method works"""
        new = PizzaEvent(
            event=self.event2,
            start=self.pizzaEvent.start + datetime.timedelta(minutes=10),
            end=timezone.now() - datetime.timedelta(hours=100),
        )
        with self.subTest(msg="end before start"):
            with self.assertRaises(ValidationError):
                new.clean()

    def test_can_not_change_if_not_in_committee(self):
        # note that if member is superuser, this might still succeed!
        self.assertFalse(
            services.can_change_order(self.member, self.pizzaEvent))

    def test_can_change_if_in_committee(self):
        self.committee.members.add(self.member)
        # refresh member object to defeat cache
        member = Member.objects.get(pk=self.member.pk)
        self.assertTrue(
            services.can_change_order(member, self.pizzaEvent))

    def test_can_change_if_member_has_organiser_override(self):
        content_type = ContentType.objects.get_for_model(Event)
        override_perm = Permission.objects.get(
            codename='override_organiser',
            content_type=content_type)
        self.member.user_permissions.add(override_perm)
        # refresh member to defeat cache
        member = Member.objects.get(pk=self.member.pk)
        self.assertTrue(
            services.can_change_order(member, self.pizzaEvent))
