from django.db import models
from utils.translation import MultilingualField, ModelTranslateMeta
from django.utils import translation
from django.test import TestCase, override_settings
from django.core.exceptions import FieldError

LANGUAGES = [
    ('en', 'English'),
    ('nl', 'Dutch'),
    ('fr', 'French'),
]


@override_settings(LANGUAGES=LANGUAGES)
class TestTranslateMeta(TestCase):

    def test_translate_adds_fields(self):
        class TestItem(models.Model, metaclass=ModelTranslateMeta):
            text = MultilingualField(models.TextField)

        self.assertTrue(hasattr(TestItem, 'text_en'))
        self.assertTrue(hasattr(TestItem, 'text_nl'))
        self.assertTrue(hasattr(TestItem, 'text_fr'))
        self.assertTrue(hasattr(TestItem, 'text'))

    def test_verbose_name_kwargs(self):
        class TestItem2(models.Model, metaclass=ModelTranslateMeta):
            text = MultilingualField(models.TextField, verbose_name='Text')

        nl = TestItem2._meta.get_field('text_nl').verbose_name
        en = TestItem2._meta.get_field('text_en').verbose_name
        fr = TestItem2._meta.get_field('text_fr').verbose_name
        self.assertIn('Text', nl)
        self.assertIn('Text', en)
        self.assertIn('Text', fr)
        self.assertEqual(len({nl, en, fr}), 3)

    def test_verbose_name_args(self):
        class TestItem3(models.Model, metaclass=ModelTranslateMeta):
            text = MultilingualField(models.TextField, 'Text')

        nl = TestItem3._meta.get_field('text_nl').verbose_name
        en = TestItem3._meta.get_field('text_en').verbose_name
        fr = TestItem3._meta.get_field('text_fr').verbose_name
        self.assertIn('Text', nl)
        self.assertIn('Text', en)
        self.assertIn('Text', fr)
        self.assertEqual(len({nl, en, fr}), 3)

    def test_no_verbose_name(self):
        class TestItem3b(models.Model, metaclass=ModelTranslateMeta):
            text = MultilingualField(models.TextField)

        nl = TestItem3b._meta.get_field('text_nl').verbose_name
        en = TestItem3b._meta.get_field('text_en').verbose_name
        fr = TestItem3b._meta.get_field('text_fr').verbose_name
        self.assertEqual('text (NL)', nl)
        self.assertEqual('text (EN)', en)
        self.assertEqual('text (FR)', fr)
        self.assertEqual(len({nl, en, fr}), 3)

    def test_other_kwargs(self):
        class TestItem4(models.Model, metaclass=ModelTranslateMeta):
            text = MultilingualField(models.CharField, 'Text', max_length=100)
        self.assertEqual(TestItem4._meta.get_field('text_nl').max_length, 100)

    def test_related_fields(self):
        for field_type in (models.ForeignKey, models.OneToOneField,
                           models.ManyToManyField):
            with self.assertRaises(NotImplementedError):
                class TestItem5(models.Model, metaclass=ModelTranslateMeta):
                    foreign = MultilingualField(field_type, 'TestItem5')

    def test_setter(self):
        class TestItem6(models.Model, metaclass=ModelTranslateMeta):
            text = MultilingualField(models.TextField)

        with self.assertRaises(AttributeError):
            TestItem6().text = 'text'  # Should not be able to set

    def test_accessor(self):
        class TestItem7(models.Model, metaclass=ModelTranslateMeta):
            text = MultilingualField(models.TextField, default='text')

        with translation.override('nl'):
            self.assertEqual(TestItem7().text, TestItem7().text_nl)

    def test_shadowing(self):
        with self.assertRaises(FieldError):
            class TestItem8(models.Model, metaclass=ModelTranslateMeta):
                text = MultilingualField(models.TextField)
                text_nl = MultilingualField(models.TextField)
