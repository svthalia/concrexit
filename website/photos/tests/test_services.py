from django.test import RequestFactory, TestCase, override_settings
from django.utils.timezone import datetime

from freezegun import freeze_time

from members.models import Member, Membership
from photos.models import Album
from photos.services import get_annotated_accessible_albums, is_album_accessible


@override_settings(SUSPEND_SIGNALS=True)
class IsAlbumAccesibleTest(TestCase):
    fixtures = ["members.json"]

    @classmethod
    def setUpTestData(cls):
        cls.member = Member.objects.filter(username="testuser").first()

    def setUp(self):
        self.rf = RequestFactory()

    @freeze_time("2017-01-01")
    def test_is_album_accessible(self):
        request = self.rf.get("/")
        request.member = None
        album = Album(date=datetime(year=2017, month=1, day=1), slug="test")

        with self.subTest(membership=None):
            self.assertFalse(is_album_accessible(request, album))

        request.member = self.member
        with self.subTest(membership=None):
            self.assertFalse(is_album_accessible(request, album))

        membership = Membership.objects.create(
            user=self.member,
            type=Membership.MEMBER,
            since=datetime(year=2016, month=1, day=1),
        )
        self.member.refresh_from_db()  # Clear the cached membership

        with self.subTest(
            membership_since=membership.since, membership_until=membership.until
        ):
            self.assertTrue(is_album_accessible(request, album))

        membership.until = datetime(year=2016, month=1, day=1)
        membership.save()
        self.member.refresh_from_db()  # Clear the cached membership

        with self.subTest(
            membership_since=membership.since, membership_until=membership.until
        ):
            self.assertFalse(is_album_accessible(request, album))

        membership.until = datetime(year=2017, month=1, day=1)
        membership.save()
        self.member.refresh_from_db()  # Clear the cached membership

        with self.subTest(
            membership_since=membership.since, membership_until=membership.until
        ):
            self.assertTrue(is_album_accessible(request, album))


@override_settings(SUSPEND_SIGNALS=True)
class GetAnnotatedAccessibleAlbumsTest(TestCase):
    fixtures = ["members.json"]

    @classmethod
    def setUpTestData(cls):
        cls.member = Member.objects.filter(username="testuser").first()

    def setUp(self):
        self.rf = RequestFactory()

    @freeze_time("2017-01-01")
    def test_get_annotated_accessible_albums(self):
        request = self.rf.get("/")
        request.member = None
        album = Album(
            title="test_case", date=datetime(year=2017, month=1, day=1), slug="test"
        )
        album.save()

        self.assertEqual(Album.objects.count(), 1)

        with self.subTest(membership=None):
            albums = Album.objects.all()
            albums = get_annotated_accessible_albums(request, albums)
            for album in albums:
                self.assertFalse(album.accessible)

        request.member = self.member
        with self.subTest(membership=None):
            albums = Album.objects.all()
            albums = get_annotated_accessible_albums(request, albums)
            for album in albums:
                self.assertFalse(album.accessible)

        membership = Membership.objects.create(
            user=self.member,
            type=Membership.MEMBER,
            since=datetime(year=2016, month=1, day=1),
        )
        self.member.refresh_from_db()  # Clear the cached membership

        with self.subTest(
            membership_since=membership.since, membership_until=membership.until
        ):
            albums = Album.objects.all()
            albums = get_annotated_accessible_albums(request, albums)
            for album in albums:
                self.assertTrue(album.accessible)

        membership.until = datetime(year=2016, month=1, day=1)
        membership.save()
        self.member.refresh_from_db()  # Clear the cached membership

        with self.subTest(
            membership_since=membership.since, membership_until=membership.until
        ):
            albums = Album.objects.all()
            albums = get_annotated_accessible_albums(request, albums)
            for album in albums:
                self.assertFalse(album.accessible)

        membership.until = datetime(year=2017, month=1, day=1)
        membership.save()
        self.member.refresh_from_db()  # Clear the cached membership

        with self.subTest(
            membership_since=membership.since, membership_until=membership.until
        ):
            albums = Album.objects.all()
            albums = get_annotated_accessible_albums(request, albums)
            for album in albums:
                self.assertTrue(album.accessible)
