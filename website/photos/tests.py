from zipfile import ZipFile
from io import BytesIO

from django.test import Client, TestCase

from members.models import Member
from photos.models import Photo, Album


def create_zip(photos):
    output_file = BytesIO()
    with ZipFile(output_file, 'w') as zip_file:
        for photo in photos:
            zip_file.write(photo)
    output_file.seek(0)
    return output_file


class AlbumUploadTest(TestCase):
    """Tests album uploads in the admin."""

    fixtures = ['members.json']

    @classmethod
    def setUpTestData(cls):
        cls.member = Member.objects.filter(user__last_name="Wiggers").first()

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.member.user)

    def test_album_upload(self):
        output_file = create_zip(["photos/fixtures/thom_assessor.png"])
        self.client.post('/admin/photos/album/add/',
                         {"title_nl": "test album",
                          "title_en": "test album",
                          "date": "2017-04-12",
                          "slug": "2017-04-12-test-album",
                          "album_archive": output_file},
                         follow=True)

        self.assertEqual(Album.objects.all().count(), 1)
        self.assertEqual(Photo.objects.all().count(), 1)

    def test_album_create_album_twice(self):
        self.client.post('/admin/photos/album/add/',
                         {"title_nl": "test album",
                          "title_en": "test album",
                          "date": "2017-04-12",
                          "slug": "2017-04-12-test-album"},
                         follow=True)
        self.client.post('/admin/photos/album/add/',
                         {"title_nl": "test album",
                          "title_en": "test album",
                          "date": "2017-04-12",
                          "slug": "2017-04-12-test-album"},
                         follow=True)

        self.assertEqual(Album.objects.all().count(), 1)

    def test_album_upload_same_photo_twice_in_album(self):
        output_file = create_zip(["photos/fixtures/thom_assessor.png"])
        self.client.post('/admin/photos/album/add/',
                         {"title_nl": "test album",
                          "title_en": "test album",
                          "date": "2017-04-12",
                          "slug": "2017-04-12-test-album",
                          "album_archive": output_file},
                         follow=True)

        pk = Album.objects.first().pk
        self.client.post('/admin/photos/album/{}/change/'.format(pk),
                         {"title_nl": "test album",
                          "title_en": "test album",
                          "date": "2017-04-12",
                          "slug": "2017-04-12-test-album",
                          "album_archive": output_file},
                         follow=True)

        self.assertEqual(Album.objects.all().count(), 1)
        self.assertEqual(Photo.objects.all().count(), 1)

    def test_album_upload_different_photo_in_album(self):
        output_file = create_zip(["photos/fixtures/thom_assessor.png"])
        self.client.post('/admin/photos/album/add/',
                         {"title_nl": "test album",
                          "title_en": "test album",
                          "date": "2017-04-12",
                          "slug": "2017-04-12-test-album",
                          "album_archive": output_file},
                         follow=True)

        output_file = create_zip(["photos/fixtures/janbeleid-hoe.jpg"])
        pk = Album.objects.first().pk
        self.client.post('/admin/photos/album/{}/change/'.format(pk),
                         {"title_nl": "test album",
                          "title_en": "test album",
                          "date": "2017-04-12",
                          "slug": "2017-04-12-test-album",
                          "album_archive": output_file},
                         follow=True)

        self.assertEqual(Album.objects.all().count(), 1)
        self.assertEqual(Photo.objects.all().count(), 2)
