import os
import datetime

from io import BytesIO
from zipfile import ZipFile

from django.conf import settings
from django.test import Client, TestCase, override_settings

from members.models import Member
from photos.models import Album, Photo


def create_zip(photos):
    valid_date = int(datetime.datetime(2019, 1, 1).timestamp())
    output_file = BytesIO()
    with ZipFile(output_file, "w") as zip_file:
        for photo in photos:
            os.utime(photo, (valid_date, valid_date))
            zip_file.write(photo)
    output_file.seek(0)
    return output_file


@override_settings(SUSPEND_SIGNALS=True)
class AlbumUploadTest(TestCase):
    """Tests album uploads in the admin."""

    fixtures = ["members.json"]

    @classmethod
    def setUpTestData(cls):
        cls.member = Member.objects.filter(last_name="Wiggers").first()

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.member)

    def test_album_upload(self):
        output_file = create_zip(
            [os.path.join(settings.BASE_DIR, "photos/fixtures/thom_assessor.png")]
        )
        self.client.post(
            "/admin/photos/album/add/",
            {
                "title": "test album",
                "date": "2017-04-12",
                "slug": "2017-04-12-test-album",
                "album_archive": output_file,
            },
            follow=True,
        )

        self.assertEqual(Album.objects.all().count(), 1)
        self.assertEqual(Photo.objects.all().count(), 1)

    def test_album_create_album_twice(self):
        self.client.post(
            "/admin/photos/album/add/",
            {
                "title": "test album",
                "date": "2017-04-12",
                "slug": "2017-04-12-test-album",
            },
            follow=True,
        )
        self.client.post(
            "/admin/photos/album/add/",
            {
                "title": "test album",
                "date": "2017-04-12",
                "slug": "2017-04-12-test-album",
            },
            follow=True,
        )

        self.assertEqual(Album.objects.all().count(), 1)

    def test_album_upload_same_photo_twice_in_album(self):
        output_file = create_zip(
            [os.path.join(settings.BASE_DIR, "photos/fixtures/thom_assessor.png")]
        )
        self.client.post(
            "/admin/photos/album/add/",
            {
                "title": "test album",
                "date": "2017-04-12",
                "slug": "2017-04-12-test-album",
                "album_archive": output_file,
            },
            follow=True,
        )

        pk = Album.objects.first().pk
        self.client.post(
            "/admin/photos/album/{}/change/".format(pk),
            {
                "title": "test album",
                "date": "2017-04-12",
                "slug": "2017-04-12-test-album",
                "album_archive": output_file,
            },
            follow=True,
        )

        self.assertEqual(Album.objects.all().count(), 1)
        self.assertEqual(Photo.objects.all().count(), 1)

    def test_album_upload_different_photo_in_album(self):
        output_file = create_zip(
            [os.path.join(settings.BASE_DIR, "photos/fixtures/thom_assessor.png")]
        )
        self.client.post(
            "/admin/photos/album/add/",
            {
                "title": "test album",
                "date": "2017-04-12",
                "slug": "2017-04-12-test-album",
                "album_archive": output_file,
            },
            follow=True,
        )

        output_file = create_zip(
            [os.path.join(settings.BASE_DIR, "photos/fixtures/janbeleid-hoe.jpg")]
        )
        pk = Album.objects.first().pk
        self.client.post(
            "/admin/photos/album/{}/change/".format(pk),
            {
                "title": "test album",
                "date": "2017-04-12",
                "slug": "2017-04-12-test-album",
                "album_archive": output_file,
            },
            follow=True,
        )

        self.assertEqual(Album.objects.all().count(), 1)
        self.assertEqual(Photo.objects.all().count(), 2)

    def test_album_upload_rotated_photo_in_album(self):
        output_file = create_zip(
            [os.path.join(settings.BASE_DIR, "photos/fixtures/rotated_janbeleid.jpg")]
        )
        self.client.post(
            "/admin/photos/album/add/",
            {
                "title": "test album",
                "date": "2017-04-12",
                "slug": "2017-04-12-test-album",
                "album_archive": output_file,
            },
            follow=True,
        )

        self.assertEqual(Photo.objects.first().rotation, 90)
