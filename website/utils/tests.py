"""Tests for the ``utils`` module"""
# pylint: disable=attribute-defined-outside-init
import doctest

from django.core.exceptions import FieldError
from django.db import models
from django.test import TestCase, override_settings
from django.utils import translation

from utils.translation import ModelTranslateMeta, MultilingualField
from utils import snippets

LANGUAGES = [
    ("en", "English"),
    ("nl", "Dutch"),
    ("fr", "French"),
]


def load_tests(_loader, tests, _ignore):
    """
    Load all tests in this module
    """
    # Adds the doctests in snippets
    tests.addTests(doctest.DocTestSuite(snippets))
    return tests


@override_settings(LANGUAGES=LANGUAGES)
class TestTranslateMeta(TestCase):
    """Test the translate metaclass"""

    def test_translate_adds_fields(self):
        """Confirm that we get extra items added to the class"""

        class _TestItem(models.Model, metaclass=ModelTranslateMeta):
            text = MultilingualField(models.TextField)

        self.assertTrue(hasattr(_TestItem, "text_en"), "expected text_en field")
        self.assertTrue(hasattr(_TestItem, "text_nl"), "expected text_nl field")
        self.assertTrue(hasattr(_TestItem, "text_fr"), "expected text_fr field")
        self.assertTrue(hasattr(_TestItem, "text"), "expect text as placeholder")

    def test_verbose_name(self):
        """
        Confirm that passing verbose_name as kwargs or args works.
        """

        class _TestItem2(models.Model, metaclass=ModelTranslateMeta):
            text = MultilingualField(models.TextField, verbose_name="Text")

        class _TestItem3(models.Model, metaclass=ModelTranslateMeta):
            text = MultilingualField(models.TextField, "Text")

        for cls in (_TestItem2, _TestItem3):
            with self.subTest(cls=cls):
                nl_name = cls._meta.get_field("text_nl").verbose_name
                en_name = cls._meta.get_field("text_en").verbose_name
                fr_name = cls._meta.get_field("text_fr").verbose_name
                self.assertIn("Text", nl_name)
                self.assertIn("Text", en_name)
                self.assertIn("Text", fr_name)
                self.assertEqual(
                    len({nl_name, en_name, fr_name}),
                    3,
                    "We expect the names to be different.",
                )

    def test_no_verbose_name(self):
        """
        Test that the generated name is processed correctly if no
        verbose_name is passed.
        """

        class _TestItem3b(models.Model, metaclass=ModelTranslateMeta):
            text = MultilingualField(models.TextField)

        nl_name = _TestItem3b._meta.get_field("text_nl").verbose_name
        en_name = _TestItem3b._meta.get_field("text_en").verbose_name
        fr_name = _TestItem3b._meta.get_field("text_fr").verbose_name
        self.assertEqual("text (NL)", nl_name)
        self.assertEqual("text (EN)", en_name)
        self.assertEqual("text (FR)", fr_name)
        self.assertEqual(
            len({nl_name, en_name, fr_name}), 3, "We expect the names to be different."
        )

    def test_other_kwargs(self):
        """Assert that other kwargs are transferred"""

        class _TestItem4(models.Model, metaclass=ModelTranslateMeta):
            text = MultilingualField(models.CharField, "Text", max_length=100)

        self.assertEqual(_TestItem4._meta.get_field("text_nl").max_length, 100)

    def test_related_fields(self):
        """Confirm that foreign keys raise errors"""
        for field_type in (
            models.ForeignKey,
            models.OneToOneField,
            models.ManyToManyField,
        ):
            with self.subTest(field_type=field_type):
                with self.assertRaises(NotImplementedError):

                    class _TestItem5(models.Model, metaclass=ModelTranslateMeta):
                        foreign = MultilingualField(field_type, "TestItem5")

    def test_setter(self):
        """Setting directly on a multilingual field is not allowed"""

        class _TestItem6(models.Model, metaclass=ModelTranslateMeta):
            text = MultilingualField(models.TextField)

        with self.assertRaises(AttributeError):
            _TestItem6().text = "text"  # Should not be able to set

        # but accessing individual language fields should work
        item = _TestItem6()

        item.text_nl = "tekst"
        item.text_en = "text"

    def test_accessor(self):
        """Test the accessor gets the proper languages"""

        class _TestItem7(models.Model, metaclass=ModelTranslateMeta):
            text = MultilingualField(models.TextField)

        item = _TestItem7()
        item.text_nl = "Hier staat tekst"
        item.text_en = "Here's some text"

        self.assertEqual(item.text_nl, "Hier staat tekst")
        self.assertEqual(item.text_en, "Here's some text")

        with translation.override("nl"):
            self.assertEqual(item.text, "Hier staat tekst")

        with translation.override("en"):
            self.assertEqual(item.text, "Here's some text")

    def test_shadowing(self):
        """Don't let us shadow a MultilingualField with another field"""
        with self.assertRaises(FieldError):

            class _TestItem8(models.Model, metaclass=ModelTranslateMeta):
                text = MultilingualField(models.TextField)
                text_nl = MultilingualField(models.TextField)
