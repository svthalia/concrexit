from unittest.mock import MagicMock

from django.test import TestCase

from registrations.templatetags.form_field import form_field


class FormFieldTemplateTagTest(TestCase):

    def test_tag(self):
        form = MagicMock()
        form.__getitem__.return_value = 'test_result'
        return_value = form_field(form, 'name')
        form.__getitem__.assert_called_once_with('name')
        self.assertEqual(return_value, {'field': 'test_result'})
