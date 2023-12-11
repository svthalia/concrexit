from django.test import Client, TestCase, override_settings

from members.models import Member
from photos.models import Album


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
