import logging
from unittest.mock import Mock

from django.core.files import File
from django.test import Client, TestCase, override_settings

from documents.models import Document
from members.models import Member


@override_settings(SUSPEND_SIGNALS=True)
class GetDocumentTest(TestCase):
    """tests for the :func:`.get_document` view."""

    fixtures = ["members.json"]

    @classmethod
    def setUpTestData(cls):
        cls.file_en = Mock(spec=File)
        cls.file_en.name = "file.pdf"
        cls.file_en.chunks.return_value = [b"file"]

        cls.document = Document.objects.create(
            pk=1,
            name="Test document (EN)",
            category="misc",
            file=cls.file_en,
        )

        cls.member = Member.objects.filter(last_name="Wiggers").first()

    def setUp(self):
        self.client = Client()
        logger = logging.getLogger("django.request")
        self.previous_log_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

    def tearDown(self):
        logger = logging.getLogger("django.request")
        logger.setLevel(self.previous_log_level)

    def test_basic(self):
        response = self.client.post("/association/documents/document/1", follow=True)
        self.assertEqual(response.status_code, 200)

    def test_does_not_exist(self):
        response = self.client.post("/association/documents/document/999", follow=True)
        self.assertEqual(response.status_code, 404)

    def test_members_only(self):
        self.document.members_only = True
        self.document.save()

        response = self.client.post("/association/documents/document/1", follow=True)
        template_names = [template.name for template in response.templates]
        self.assertIn("two_factor/core/login.html", template_names)

        self.client.force_login(self.member)

        response = self.client.post("/association/documents/document/1", follow=True)
        template_names = [template.name for template in response.templates]
        self.assertNotIn("two_factor/core/login.html", template_names)
