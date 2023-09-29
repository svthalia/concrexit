from unittest.mock import patch

from django.test import TestCase

from thaliawebsite.tasks import clear_tokens


class CeleryTest(TestCase):
    @patch("thaliawebsite.tasks.clear_expired")
    def test_clear_tokens(self, mock_clear_tokens):
        clear_tokens()
        mock_clear_tokens.assert_called_once()
