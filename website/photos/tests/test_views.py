import os

from datetime import date

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings

from members.models import Member, Membership
from photos.models import Album, Photo
from photos.services import save_photo


@override_settings(SUSPEND_SIGNALS=True)
class AlbumIndexTest(TestCase):

    fixtures = ["members.json"]

    @classmethod
    def setUpTestData(cls):
        cls.member = Member.objects.filter(last_name="Wiggers").first()
        cls.client = Client()

    def setUp(self):
        self.client.force_login(self.member)

    def test_index(self):
        with self.subTest(album_objects__count=Album.objects.count()):
            response = self.client.get(reverse("photos:index"))
            self.assertEqual(response.status_code, 200)

        for i in range(12):
            Album.objects.create(
                title="test_album_a%d" % i,
                date=date(year=2018, month=9, day=5),
                slug="test_album_a%d" % i,
            )

        with self.subTest(album_objects__count=Album.objects.count()):
            response = self.client.get(reverse("photos:index"))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.context["albums"]), 12)
            self.assertEqual(response.context["page_range"], range(1, 2))

        for i in range(12):
            Album.objects.create(
                title="test_album_b%d" % i,
                date=date(year=2018, month=9, day=5),
                slug="test_album_b%d" % i,
            )

        with self.subTest(album_objects__count=Album.objects.count()):
            response = self.client.get(reverse("photos:index"))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.context["albums"]), 16)
            self.assertEqual(response.context["page_range"], range(1, 3))

        for i in range(72):
            Album.objects.create(
                title="test_album_c%d" % i,
                date=date(year=2018, month=9, day=5),
                slug="test_album_c%d" % i,
            )

        with self.subTest(album_objects__count=Album.objects.count()):
            response = self.client.get(reverse("photos:index"))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.context["albums"]), 16)
            self.assertEqual(response.context["page_range"], range(1, 6))

    def test_empty_page(self):
        Album.objects.create(
            title="test_album", date=date(year=2018, month=9, day=5), slug="test_album",
        )

        response = self.client.get(reverse("photos:index") + "?page=5")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_range"], range(1, 2))

    def test_keywords(self):
        Album.objects.create(
            title="test_album1",
            date=date(year=2018, month=9, day=5),
            slug="test_album1",
        )

        Album.objects.create(
            title="test_album12",
            date=date(year=2018, month=9, day=5),
            slug="test_album2",
        )

        Album.objects.create(
            title="test_album3",
            date=date(year=2018, month=9, day=5),
            slug="test_album3",
        )

        for (count, keywords) in [(3, ""), (2, "1"), (1, "12"), (1, "3")]:
            with self.subTest(keywords=keywords):
                response = self.client.get(
                    reverse("photos:index") + "?keywords={}".format(keywords)
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(len(response.context["albums"]), count)
                self.assertEqual(response.context["page_range"], range(1, 2))

    def test_many_pages(self):
        for i in range(120):
            Album.objects.create(
                title="test_album_%d" % i,
                date=date(year=2018, month=9, day=5),
                slug="test_album_%d" % i,
            )

        with self.subTest(page=1):
            response = self.client.get(reverse("photos:index") + "?page=1")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.context["albums"]), 16)
            self.assertEqual(response.context["page_range"], range(1, 6))

        with self.subTest(page=4):
            response = self.client.get(reverse("photos:index") + "?page=4")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.context["albums"]), 16)
            self.assertEqual(response.context["page_range"], range(2, 7))

        with self.subTest(page=9):
            response = self.client.get(reverse("photos:index") + "?page=9")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.context["albums"]), 8)
            self.assertEqual(response.context["page_range"], range(4, 9))


@override_settings(SUSPEND_SIGNALS=True)
class AlbumTest(TestCase):

    fixtures = ["members.json"]

    @classmethod
    def setUpTestData(cls):
        cls.member = Member.objects.filter(username="testuser").first()
        cls.client = Client()

    def setUp(self):
        self.album = Album.objects.create(
            title="test_album", date=date(year=2017, month=9, day=5), slug="test_album",
        )

        self.client.force_login(self.member)

    def test_get(self):
        Membership.objects.create(
            type=Membership.MEMBER,
            user=self.member,
            since=date(year=2015, month=1, day=1),
            until=None,
        )

        for i in range(10):
            with open(
                os.path.join(settings.BASE_DIR, "photos/fixtures/thom_assessor.png"),
                "rb",
            ) as f:
                fi = SimpleUploadedFile(
                    name="photo{}.png".format(i),
                    content=f.read(),
                    content_type="image/png",
                )
                photo = Photo(album=self.album, file=fi)
                photo.save()

        response = self.client.get(reverse("photos:album", args=(self.album.slug,)))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["album"], self.album)
        self.assertEqual(len(response.context["photos"]), 10)

    def test_unaccessible(self):
        Membership.objects.create(
            type=Membership.MEMBER,
            user=self.member,
            since=date(year=2016, month=1, day=1),
            until=date(year=2018, month=1, day=1),
        )

        with self.subTest():
            self.album.date = date(year=2017, month=1, day=1)
            self.album.save()

            response = self.client.get(reverse("photos:album", args=(self.album.slug,)))
            self.assertEqual(response.status_code, 200)

        with self.subTest():
            self.album.date = date(year=2018, month=9, day=5)
            self.album.save()

            response = self.client.get(reverse("photos:album", args=(self.album.slug,)))
            self.assertEqual(response.status_code, 404)


@override_settings(SUSPEND_SIGNALS=True)
class SharedAlbumTest(TestCase):

    fixtures = ["members.json"]

    @classmethod
    def setUpTestData(cls):
        cls.member = Member.objects.filter(username="testuser").first()
        cls.client = Client()

    def setUp(self):
        self.album = Album.objects.create(
            title="test_album",
            date=date(year=2017, month=9, day=5),
            shareable=True,
            slug="test_album",
        )

    def test_get(self):
        for i in range(10):
            with open(
                os.path.join(settings.BASE_DIR, "photos/fixtures/thom_assessor.png"),
                "rb",
            ) as f:
                fi = SimpleUploadedFile(
                    name="photo{}.png".format(i),
                    content=f.read(),
                    content_type="image/png",
                )
                photo = Photo(album=self.album, file=fi)
                photo.save()

        response = self.client.get(
            reverse(
                "photos:shared-album", args=(self.album.slug, self.album.access_token,)
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["album"], self.album)
        self.assertEqual(len(response.context["photos"]), 10)


@override_settings(SUSPEND_SIGNALS=True)
class DownloadTest(TestCase):

    fixtures = ["members.json"]

    @classmethod
    def setUpTestData(cls):
        cls.member = Member.objects.filter(last_name="Wiggers").first()

    def setUp(self):
        self.client = Client()

        self.album = Album.objects.create(
            title="test_album", date=date(year=2017, month=9, day=5), slug="test_album",
        )

        with open(
            os.path.join(settings.BASE_DIR, "photos/fixtures/thom_assessor.png"), "rb"
        ) as f:
            fi = SimpleUploadedFile(
                name="photo.png", content=f.read(), content_type="image/png"
            )

        self.photo = Photo(album=self.album)
        self.photo.file.save(fi.name, fi)
        save_photo(self.photo)

    def test_download(self):
        self.client.force_login(self.member)

        response = self.client.get(
            reverse("photos:download", args=(self.album.slug, self.photo,))
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/jpeg")

    def test_logged_out(self):
        response = self.client.get(
            reverse("photos:download", args=(self.album.slug, self.photo,))
        )
        self.assertEqual(response.status_code, 302)


class _DownloadBaseTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        self.album = Album.objects.create(
            title="test_album", date=date(year=2017, month=9, day=5), slug="test_album",
        )

        with open(
            os.path.join(settings.BASE_DIR, "photos/fixtures/thom_assessor.png"), "rb"
        ) as f:
            fi = SimpleUploadedFile(
                name="photo.png", content=f.read(), content_type="image/png"
            )

        self.photo = Photo(album=self.album)
        self.photo.file.save(fi.name, fi)
        save_photo(self.photo)


@override_settings(SUSPEND_SIGNALS=True)
class SharedDownloadTest(_DownloadBaseTestCase):

    fixtures = ["members.json"]

    @classmethod
    def setUpTestData(cls):
        cls.member = Member.objects.filter(last_name="Wiggers").first()
        cls.client = Client()

    def test_download(self):
        with self.subTest():
            response = self.client.get(
                reverse(
                    "photos:shared-download",
                    args=(self.album.slug, self.album.access_token, self.photo,),
                )
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response["Content-Type"], "image/jpeg")

        self.client.force_login(self.member)

        with self.subTest():
            response = self.client.get(
                reverse(
                    "photos:shared-download",
                    args=(self.album.slug, self.album.access_token, self.photo,),
                )
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response["Content-Type"], "image/jpeg")
