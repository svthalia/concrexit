import shutil
import tempfile

from django.core.files import File
from django.conf import settings
from django.test import TestCase

from .models import Thabloid


class TestThabloid(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._old_media_root = settings.MEDIA_ROOT
        settings.MEDIA_ROOT = tempfile.mkdtemp()
        cls.thabloid = Thabloid(
            year=1998,
            issue=1,
            file=File(open('thabloid/fixtures/thabloid-1998-1999-1.pdf',
                           'rb')))
        # Only generate pages if we have 'gs'
        if shutil.which('gs') is None:
            cls.thabloid.save(nopages=True)
        else:
            # we should wait for gs to be done before we can do cleanup
            cls.thabloid.save(wait=True)

    @classmethod
    def tearDownClass(cls):
        """Clean up remaining Thabloid files"""
        shutil.rmtree(settings.MEDIA_ROOT)
        settings.MEDIA_ROOT = cls._old_media_root
        super().tearDownClass()

    def test_thaboid_get_absolute_url(self):
        self.assertEqual(self.thabloid.get_absolute_url(),
                         '/thabloid/pages/1998/1/')

    def test_page_urls(self):
        self.assertEqual(
            self.thabloid.cover,
            'public/thabloids/pages/thabloid-1998-1999-1/001.jpg')
        self.assertEqual(
            self.thabloid.page_url(2),
            'public/thabloids/pages/thabloid-1998-1999-1/002.jpg')
        # check if it's actual zeropadding and not just '00' + i
        self.assertEqual(
            self.thabloid.page_url(20),
            'public/thabloids/pages/thabloid-1998-1999-1/020.jpg')
