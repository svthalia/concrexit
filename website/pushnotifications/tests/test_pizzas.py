from django.test import TestCase
from django.utils import timezone

from events import payables
from events.models import Event, EventRegistration
from members.models import Member, Membership, Profile
from pizzas.models import FoodEvent, FoodOrder, Product
from pushnotifications.models import FoodOrderReminderMessage


class TestFoodEventNotifications(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.time = timezone.now()
        cls.member = Member.objects.create(username="user1")
        Profile.objects.create(user=cls.member)
        Membership.objects.create(
            user=cls.member, type=Membership.MEMBER, since="2000-01-01"
        )

        cls.member2 = Member.objects.create(username="user2")
        Profile.objects.create(user=cls.member2)
        Membership.objects.create(
            user=cls.member2, type=Membership.MEMBER, since="2000-01-01"
        )

        cls.not_current_member = Member.objects.create(username="user3")
        Profile.objects.create(user=cls.not_current_member)

        cls.event = Event.objects.create(
            title="Test event",
            start=cls.time + timezone.timedelta(days=1),
            end=cls.time + timezone.timedelta(days=2),
        )

        cls.product = Product.objects.create(name="Test product", price=10)

    def setUp(self):
        payables.register()

    def test_create_food_event_schedules_notification(self):
        """Creating a food event schedules a notification with the right users."""
        with self.subTest("send_notification=True, registration not required"):
            food_event = FoodEvent.objects.create(
                event=self.event,
                send_notification=True,
                start=self.time + timezone.timedelta(days=1),
                end=self.time + timezone.timedelta(days=2),
            )

            self.assertIsNotNone(food_event.end_reminder)
            self.assertIn(self.member, food_event.end_reminder.users.all())
            self.assertIn(self.member2, food_event.end_reminder.users.all())
            self.assertNotIn(
                self.not_current_member, food_event.end_reminder.users.all()
            )

        food_event.delete()

        with self.subTest("send_notification=False, registration not required"):
            food_event = FoodEvent.objects.create(
                event=self.event,
                send_notification=False,
                start=self.time + timezone.timedelta(days=1),
                end=self.time + timezone.timedelta(days=2),
            )

            self.assertFalse(hasattr(food_event, "end_reminder"))
            self.assertFalse(
                FoodOrderReminderMessage.objects.filter(food_event=food_event).exists()
            )

        food_event.delete()

        self.event.registration_start = self.time - timezone.timedelta(days=1)
        self.event.registration_end = self.time
        self.event.save()

        EventRegistration.objects.create(event=self.event, member=self.member)

        with self.subTest("send_notification=True, registration required"):
            food_event = FoodEvent.objects.create(
                event=self.event,
                send_notification=True,
                start=self.time + timezone.timedelta(days=1),
                end=self.time + timezone.timedelta(days=2),
            )

            self.assertIsNotNone(food_event.end_reminder)
            self.assertIn(self.member, food_event.end_reminder.users.all())
            self.assertNotIn(self.member2, food_event.end_reminder.users.all())
            self.assertNotIn(
                self.not_current_member, food_event.end_reminder.users.all()
            )

        food_event.delete()

        with self.subTest("send_notification=False, registration required"):
            food_event = FoodEvent.objects.create(
                event=self.event,
                send_notification=False,
                start=self.time + timezone.timedelta(days=1),
                end=self.time + timezone.timedelta(days=2),
            )

            self.assertFalse(hasattr(food_event, "end_reminder"))
            self.assertFalse(
                FoodOrderReminderMessage.objects.filter(food_event=food_event).exists()
            )

        food_event.delete()

    def test_update_food_event(self):
        """Updating the event creates or deletes the notification."""
        food_event = FoodEvent.objects.create(
            event=self.event,
            send_notification=False,
            start=self.time + timezone.timedelta(days=1),
            end=self.time + timezone.timedelta(days=2),
        )

        self.assertFalse(hasattr(food_event, "end_reminder"))

        food_event.send_notification = True
        food_event.save()

        self.assertIsNotNone(food_event.end_reminder)

        food_event.send_notification = False
        food_event.save()

        self.assertFalse(hasattr(food_event, "end_reminder"))

        food_event.send_notification = True
        food_event.save()

        food_event.end = self.time
        food_event.save()

        self.assertFalse(hasattr(food_event, "end_reminder"))

    def test_register_updates_message_users(self):
        """Registering for an event updates the notification users."""
        self.event.registration_start = self.time - timezone.timedelta(days=1)
        self.event.registration_end = self.time
        self.event.save()

        food_event = FoodEvent.objects.create(
            event=self.event,
            send_notification=True,
            start=self.time + timezone.timedelta(days=1),
            end=self.time + timezone.timedelta(days=2),
        )

        self.assertIsNotNone(food_event.end_reminder)
        self.assertNotIn(self.member2, food_event.end_reminder.users.all())

        registration = EventRegistration.objects.create(
            event=self.event, member=self.member2
        )

        self.assertIn(self.member2, food_event.end_reminder.users.all())

        registration.date_cancelled = timezone.now()
        registration.save()

        self.assertNotIn(self.member2, food_event.end_reminder.users.all())

    def test_order_updates_message_users(self):
        """Ordering food updates the notification users."""
        food_event = FoodEvent.objects.create(
            event=self.event,
            send_notification=True,
            start=self.time + timezone.timedelta(days=1),
            end=self.time + timezone.timedelta(days=2),
        )

        self.assertIsNotNone(food_event.end_reminder)
        self.assertIn(self.member, food_event.end_reminder.users.all())

        order = FoodOrder.objects.create(
            food_event=food_event, member=self.member, product=self.product
        )

        self.assertNotIn(self.member, food_event.end_reminder.users.all())

        order.delete()

        self.assertIn(self.member, food_event.end_reminder.users.all())
