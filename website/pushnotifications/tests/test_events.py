from django.test import TestCase
from django.utils import timezone

from events.models import Event, EventRegistration
from members.models import Member, Membership, Profile


class TestEventNotifications(TestCase):
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

    def test_create_event_and_update_registrations_start_reminder(self):
        """Creating an event schedules a start reminder for the right users.

        Creating, cancelling and deleting"""

        with self.subTest("past event"):
            event = Event.objects.create(
                title="Test event",
                start=self.time - timezone.timedelta(days=2),
                end=self.time - timezone.timedelta(days=1),
                published=True,
            )

            self.assertFalse(hasattr(event, "start_reminder"))

        with self.subTest("registration not required, published=False"):
            event = Event.objects.create(
                title="Test event",
                start=self.time + timezone.timedelta(days=1),
                end=self.time + timezone.timedelta(days=2),
            )

            self.assertFalse(hasattr(event, "start_reminder"))

        with self.subTest("registration required, published=False"):
            event = Event.objects.create(
                title="Test event",
                start=self.time + timezone.timedelta(days=1),
                end=self.time + timezone.timedelta(days=2),
                registration_start=self.time - timezone.timedelta(days=1),
                registration_end=self.time,
            )

            self.assertFalse(hasattr(event, "start_reminder"))

        with self.subTest("registration not required, published=True"):
            event = Event.objects.create(
                title="Test event",
                start=self.time + timezone.timedelta(days=1),
                end=self.time + timezone.timedelta(days=2),
                published=True,
            )

            self.assertIsNotNone(event.start_reminder)
            self.assertIn(self.member, event.start_reminder.users.all())
            self.assertIn(self.member2, event.start_reminder.users.all())
            self.assertNotIn(self.not_current_member, event.start_reminder.users.all())

            registration = EventRegistration.objects.create(
                event=event, member=self.member, date=self.time
            )

            self.assertIn(self.member, event.start_reminder.users.all())

            registration.date_cancelled = timezone.now()
            registration.save()

            self.assertIn(self.member, event.start_reminder.users.all())

            registration2 = EventRegistration.objects.create(
                event=event, member=self.member2, date=self.time
            )
            registration2.delete()

            self.assertIn(self.member2, event.start_reminder.users.all())

        with self.subTest("registration required, published=True"):
            event = Event.objects.create(
                title="Test event",
                start=self.time + timezone.timedelta(days=1),
                end=self.time + timezone.timedelta(days=2),
                registration_start=self.time - timezone.timedelta(days=1),
                registration_end=self.time,
                published=True,
            )

            self.assertIsNotNone(event.start_reminder)
            self.assertNotIn(self.member, event.start_reminder.users.all())
            self.assertNotIn(self.member2, event.start_reminder.users.all())
            self.assertNotIn(self.not_current_member, event.start_reminder.users.all())

            registration = EventRegistration.objects.create(
                event=event, member=self.member, date=self.time
            )

            self.assertIn(self.member, event.start_reminder.users.all())

            registration.date_cancelled = timezone.now()
            registration.save()

            self.assertNotIn(self.member, event.start_reminder.users.all())

            registration.date_cancelled = None
            registration.save()

            self.assertIn(self.member, event.start_reminder.users.all())

            registration.delete()

            self.assertNotIn(self.member2, event.start_reminder.users.all())

    def test_update_event_start_reminder(self):
        """Updating an event creates, deletes or updates the start reminder correctly."""
        event = Event.objects.create(
            title="Test event",
            start=self.time + timezone.timedelta(days=1),
            end=self.time + timezone.timedelta(days=2),
            published=True,
        )

        self.assertIsNotNone(event.start_reminder)

        event.published = False
        event.save()

        self.assertFalse(hasattr(event, "start_reminder"))

        event.published = True
        event.save()

        self.assertIsNotNone(event.start_reminder)

        event.start = self.time - timezone.timedelta(days=1)
        event.save()

        self.assertFalse(hasattr(event, "start_reminder"))

    def test_create_event_registration_reminder(self):
        """Creating an event that requires registration schedules registration reminder."""

        with self.subTest("past registration period"):
            event = Event.objects.create(
                title="Test event",
                start=self.time + timezone.timedelta(days=2),
                end=self.time + timezone.timedelta(days=3),
                registration_start=self.time - timezone.timedelta(days=2),
                registration_end=self.time - timezone.timedelta(days=1),
                published=True,
            )

            self.assertFalse(hasattr(event, "registration_reminder"))

        with self.subTest("registration required, published=True"):
            event = Event.objects.create(
                title="Test event",
                start=self.time + timezone.timedelta(days=2),
                end=self.time + timezone.timedelta(days=3),
                registration_start=self.time + timezone.timedelta(days=1),
                registration_end=self.time + timezone.timedelta(days=2),
                published=True,
            )

            self.assertIsNotNone(event.registration_reminder)
            self.assertIn(self.member, event.registration_reminder.users.all())
            self.assertIn(self.member2, event.registration_reminder.users.all())
            self.assertNotIn(
                self.not_current_member, event.registration_reminder.users.all()
            )

        with self.subTest("registration required, published=False"):
            event = Event.objects.create(
                title="Test event",
                start=self.time + timezone.timedelta(days=2),
                end=self.time + timezone.timedelta(days=3),
                registration_start=self.time + timezone.timedelta(days=1),
                registration_end=self.time + timezone.timedelta(days=2),
            )

            self.assertFalse(hasattr(event, "registration_reminder"))

        with self.subTest("registration not required, published=True"):
            event = Event.objects.create(
                title="Test event",
                start=self.time + timezone.timedelta(days=2),
                end=self.time + timezone.timedelta(days=3),
                published=True,
            )

            self.assertFalse(hasattr(event, "registration_reminder"))

    def test_update_event_registration_reminder(self):
        """Updating an event creates, deletes or updates the registration reminder correctly."""
        event = Event.objects.create(
            title="Test event",
            start=self.time + timezone.timedelta(days=2),
            end=self.time + timezone.timedelta(days=3),
            registration_start=self.time + timezone.timedelta(days=1),
            registration_end=self.time + timezone.timedelta(days=2),
            published=True,
        )

        self.assertIsNotNone(event.registration_reminder)

        event.published = False
        event.save()

        self.assertFalse(hasattr(event, "registration_reminder"))

        event.published = True
        event.save()

        self.assertIsNotNone(event.registration_reminder)

        event.registration_start = self.time - timezone.timedelta(days=1)
        event.save()

        self.assertFalse(hasattr(event, "registration_reminder"))
