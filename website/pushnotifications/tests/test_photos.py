from django.test import TestCase

from members.models import Member, Membership, Profile
from photos.models import Album
from pushnotifications.models import NewAlbumMessage


class TestNewAlbumNotifications(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.member = Member.objects.create(username="user1")
        Profile.objects.create(user=cls.member)
        Membership.objects.create(
            user=cls.member, type=Membership.MEMBER, since="2000-01-01"
        )

        cls.not_current_member = Member.objects.create(username="user2")
        Profile.objects.create(user=cls.not_current_member)

    def test_new_published_album_schedules_notification(self):
        """Creating a new album schedules a notification to all members."""
        album = Album.objects.create(
            slug="test-album",
            title="test album",
            date="2000-01-01",
            hidden=False,
            is_processing=False,
        )

        self.assertIsNotNone(album.new_album_notification)
        self.assertIn(self.member, album.new_album_notification.users.all())
        self.assertNotIn(
            self.not_current_member, album.new_album_notification.users.all()
        )

    def test_new_hidden_album_does_not_schedule_notification(self):
        """Creating a new hidden album does not schedule a notification."""
        album = Album.objects.create(
            slug="test-album",
            title="test album",
            date="2000-01-01",
            hidden=True,
        )

        self.assertFalse(hasattr(album, "new_album_notification"))
        self.assertFalse(NewAlbumMessage.objects.filter(album=album).exists())

    def test_new_uploading_album_does_not_schedule_notification(self):
        """Creating a new hidden album does not schedule a notification."""
        album = Album.objects.create(
            slug="test-album",
            title="test album",
            date="2000-01-01",
            hidden=False,
            is_processing=True,
        )

        self.assertFalse(hasattr(album, "new_album_notification"))
        self.assertFalse(NewAlbumMessage.objects.filter(album=album).exists())

    def test_hide_album_deletes_notification(self):
        """Hiding an album deletes the scheduled notification."""
        album = Album.objects.create(
            slug="test-album",
            title="test album",
            date="2000-01-01",
            hidden=False,
        )

        self.assertIsNotNone(album.new_album_notification)

        album.hidden = True
        album.save()

        self.assertFalse(hasattr(album, "new_album_notification"))
        self.assertFalse(NewAlbumMessage.objects.filter(album=album).exists())

    def test_unhide_album_schedules_notification(self):
        """Unhiding an album schedules a notification to all members."""
        album = Album.objects.create(
            slug="test-album",
            title="test album",
            date="2000-01-01",
            hidden=True,
        )

        self.assertFalse(hasattr(album, "new_album_notification"))

        album.hidden = False
        album.save()

        self.assertIsNotNone(album.new_album_notification)
        self.assertIn(self.member, album.new_album_notification.users.all())
        self.assertNotIn(
            self.not_current_member, album.new_album_notification.users.all()
        )
