import os.path
import shutil
import tempfile

from django.conf import settings
from django.core.files import File
from django.test import TestCase
from django.test.utils import override_settings

from thabloid.models import Thabloid

tmp_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=tmp_MEDIA_ROOT)
class TestThabloid(TestCase):
    def setUp(self):
        with open(
            os.path.join(
                settings.BASE_DIR, "thabloid/fixtures/thabloid-1998-1999-1.pdf"
            ),
            "rb",
        ) as f:
            self.thabloid = Thabloid(year=1998, issue=1, file=File(f))
            # we should wait for gs to be done before we can do cleanup
            self.thabloid.save(wait=True)

    def tearDown(self):
        """Clean up remaining Thabloid files."""
        shutil.rmtree(settings.MEDIA_ROOT)

    def test_thaboid_get_absolute_url(self):
        self.assertEqual(
            self.thabloid.get_absolute_url(), "/members/thabloid/pages/1998/1/"
        )

    def test_page_urls(self):
        self.assertEqual(
            self.thabloid.cover, "private/thabloids/pages/thabloid-1998-1999-1/001.png"
        )
        self.assertEqual(
            self.thabloid.page_url(2, 3),
            "private/thabloids/pages/thabloid-1998-1999-1/002-003.png",
        )
        # check if it's actual zeropadding and not just '00' + i
        self.assertEqual(
            self.thabloid.page_url(20),
            "private/thabloids/pages/thabloid-1998-1999-1/020.png",
        )

    @staticmethod
    def _pdf_exist(pdf):
        pdf = pdf.lstrip(settings.MEDIA_URL)
        return os.path.isfile(os.path.join(settings.MEDIA_ROOT, pdf))

    @staticmethod
    def _jpgs_exist(pages, inverse=False):
        jpgs = [url.lstrip(settings.MEDIA_URL) for url in pages]
        for jpg in jpgs:
            jpgpath = os.path.join(settings.MEDIA_ROOT, jpg)
            if (not inverse and not os.path.isfile(jpgpath)) or (
                inverse and os.path.isfile(jpgpath)
            ):
                return False
        return True

    def test_pdf_existence(self):
        TestThabloid._pdf_exist(self.thabloid.file.url)

    def test_jpg_existence(self):
        TestThabloid._jpgs_exist(self.thabloid.pages)

    def test_change_year(self):
        self.thabloid.year += 1
        self.thabloid.save()
        self.assertTrue(TestThabloid._pdf_exist(self.thabloid.file.url))
        self.assertTrue(TestThabloid._jpgs_exist(self.thabloid.pages))

    def test_change_year_cleanup(self):
        oldpages = list(self.thabloid.pages)
        oldurl = self.thabloid.file.url
        self.thabloid.year += 1
        self.thabloid.save()
        self.assertFalse(TestThabloid._pdf_exist(oldurl))
        self.assertTrue(TestThabloid._jpgs_exist(oldpages, inverse=True))

    def test_change_issue(self):
        self.thabloid.issue += 1
        self.thabloid.save()
        self.assertTrue(TestThabloid._pdf_exist(self.thabloid.file.url))
        self.assertTrue(TestThabloid._jpgs_exist(self.thabloid.pages))

    def test_change_issue_cleanup(self):
        oldpages = list(self.thabloid.pages)
        oldurl = self.thabloid.file.url
        self.thabloid.issue += 1
        self.thabloid.save()
        self.assertFalse(TestThabloid._pdf_exist(oldurl))
        self.assertTrue(TestThabloid._jpgs_exist(oldpages, inverse=True))
