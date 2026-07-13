import datetime

from django.contrib.auth.models import ContentType, Permission
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone, translation
from django.conf import settings

from freezegun import freeze_time

from activemembers.models import Committee
from events.models import Event
from members.models import Member
from pizzas import services
from pizzas.models import FoodEvent, FoodOrder, Product


@freeze_time("2018-03-21")
@override_settings(SUSPEND_SIGNALS=True)
class PizzaEventTestCase(TestCase):
    """Test the pizzaevent class."""

    fixtures = ["members.json", "member_groups.json"]

    @classmethod
    def setUpTestData(cls):
        # set up user with change_order perm
        cls.member = Member.objects.get(pk=3)  # a non-superuser
        content_type = ContentType.objects.get_for_model(FoodOrder)
        cls.change_order_perm = Permission.objects.get(
            codename="change_foodorder", content_type=content_type
        )
        cls.member.user_permissions.add(cls.change_order_perm)

        cls.committee = Committee.objects.get(pk=1)
        cls.event = Event.objects.create(
            title="testevent en",
            description="desc",
            start=(timezone.now() + datetime.timedelta(hours=1)),
            end=(timezone.now() + datetime.timedelta(hours=2)),
            location="test location",
            map_location="test map location",
            price=0.00,
            fine=5.00,
        )
        cls.event.organisers.add(cls.committee)

        cls.event2 = Event.objects.create(
            title="testevent2 en",
            description="desc2",
            start=(timezone.now() + datetime.timedelta(hours=4)),
            end=(timezone.now() + datetime.timedelta(hours=8)),
            location="test location2",
            map_location="test map location",
            price=0.00,
            fine=5.00,
        )
        cls.event2.organisers.add(cls.committee)

        cls.food_event = FoodEvent.objects.create(
            event=cls.event,
            start=timezone.now() - datetime.timedelta(hours=1),
            end=timezone.now() + datetime.timedelta(hours=2),
        )

    def test_title(self):
        """Check the title attribute."""
        with self.subTest(lang="en"):
            translation.activate("en")
            self.assertEqual(self.food_event.title, self.event.title)

    def test_current(self):
        """Test the classmethod that fetches a currently active pizzaevent."""
        with self.subTest(msg="Single event, active"):
            self.assertEqual(self.food_event, FoodEvent.current())

        with self.subTest(mgs="Single event, not active"):
            self.food_event.start = timezone.now() + datetime.timedelta(hours=10)
            self.food_event.end = timezone.now() + datetime.timedelta(hours=100)
            self.food_event.save()
            self.assertIsNone(FoodEvent.current())

        second_pizzaevent = FoodEvent.objects.create(
            start=timezone.now() + datetime.timedelta(hours=100),
            end=timezone.now() + datetime.timedelta(hours=1000),
            event=self.event2,
        )

        with self.subTest(msg="two events, not active"):
            self.assertIsNone(FoodEvent.current())

        self.food_event.start = timezone.now() - datetime.timedelta(hours=1)
        self.food_event.end = timezone.now() + datetime.timedelta(hours=1)
        self.food_event.save()

        with self.subTest(msg="two events, one active"):
            self.assertEqual(self.food_event, FoodEvent.current())

        second_pizzaevent.start = timezone.now() + datetime.timedelta(hours=2)
        second_pizzaevent.save()
        with self.subTest(msg="two events, within 8 hours"):
            self.assertEqual(self.food_event, FoodEvent.current())

        self.food_event.end = timezone.now() - datetime.timedelta(minutes=10)
        self.food_event.save()
        with self.subTest(msg="two events, within 8 hours, first ended"):
            self.assertEqual(second_pizzaevent, FoodEvent.current())

    def test_validate_unique(self):
        """Check if uniqueness validation is correct."""
        self.food_event.start = self.food_event.start + datetime.timedelta(minutes=10)

        with self.subTest(msg="saving works"):
            self.food_event.validate_unique()

        new = FoodEvent(
            event=self.event2,
            start=self.food_event.start + datetime.timedelta(minutes=10),
            end=timezone.now() + datetime.timedelta(hours=100),
        )
        with self.subTest(msg="overlapping event"):
            with self.assertRaises(ValidationError):
                new.validate_unique()

    def test_clean(self):
        """Check if clean method works."""
        new = FoodEvent(
            event=self.event2,
            start=self.food_event.start + datetime.timedelta(minutes=10),
            end=timezone.now() - datetime.timedelta(hours=100),
        )
        with self.subTest(msg="end before start"):
            with self.assertRaises(ValidationError):
                new.clean()

    def test_can_not_change_if_not_in_committee(self):
        # note that if member is superuser, this might still succeed!
        self.assertFalse(services.can_change_order(self.member, self.food_event))

    def test_can_change_if_in_committee(self):
        self.committee.members.add(self.member)
        # refresh member object to defeat cache
        member = Member.objects.get(pk=self.member.pk)
        self.assertTrue(services.can_change_order(member, self.food_event))

    def test_can_change_if_member_has_organiser_override(self):
        content_type = ContentType.objects.get_for_model(Event)
        override_perm = Permission.objects.get(
            codename="override_organiser", content_type=content_type
        )
        self.member.user_permissions.add(override_perm)
        # refresh member to defeat cache
        member = Member.objects.get(pk=self.member.pk)
        self.assertTrue(services.can_change_order(member, self.food_event))

    def test_data_minimisation(self):

        p1 = Product.objects.create(
            name="test",
            description="test descr",
            price=1.00
        )

        with self.subTest("FoodOrders older than 3 years should be minimised"):
            e1 = Event.objects.create(
            pk=10,
            title="testevent",
            description="desc",
            published=True,
            start=(timezone.now() - datetime.timedelta(days=(settings.DATA_RETENTION_PERIODS["FOOD"]) + 1)), #should be minimised
            end=(timezone.now() - datetime.timedelta(days=(settings.DATA_RETENTION_PERIODS["FOOD"]) + 2)),
            location="test location",
            map_location="test map location",
            price=0.00,
            fine=0.00,
            )

            fo1 = FoodEvent.objects.create(
                start=e1.start,
                end=e1.end,
                event=e1,
            )

            o1 = FoodOrder.objects.create(
                member=self.member,
                food_event=fo1,
                product=p1,
            )

            result = services.execute_data_minimisation(dry_run=True)

            self.assertTrue(result.filter(pk=o1.pk).exists())

        with self.subTest("FoodOrders not older than 3 years should not be minimised"):
            e2 = Event.objects.create(
            pk=11,
            title="testevent",
            description="desc",
            published=True,
            start=(timezone.now() - datetime.timedelta(days=(settings.DATA_RETENTION_PERIODS["FOOD"]) -2)), #should not be minimised
            end=(timezone.now() - datetime.timedelta(days=(settings.DATA_RETENTION_PERIODS["FOOD"]) - 1)),
            location="test location",
            map_location="test map location",
            price=0.00,
            fine=0.00,
            )

            fo2 = FoodEvent.objects.create(
                start=e2.start,
                end=e2.end,
                event=e2,
            )

            o2 = FoodOrder.objects.create(
                member=self.member,
                food_event=fo2,
                product=p1,
            )

            result = services.execute_data_minimisation(dry_run=True)

            self.assertFalse(result.filter(pk=o2.pk).exists())


