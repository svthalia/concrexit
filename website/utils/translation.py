"""
This module makes it easy to define translatable model fields.

To use it in a ``models.py``, make sure you;
  - set the metaclass of your model to :class:`ModelTranslateMeta`
  - replace any translatable model fields by :class:`MultilingualField`
    instances
  - make and apply database migrations

See the following usage example;

.. code:: python

    from django.db import models
    from utils.translation import MultilingualField, ModelTranslateMeta

    class SomeItem(models.Model, metaclass=ModelTranslateMeta):

        name = MultilingualField(models.CharField, max_length=100)
        description = MultilingualField(models.TextField)

In order to use the fields in :class:`~django.contrib.admin.ModelAdmin`
configuration (such as in the ``fields``, ``fieldsets`` or
``prepopulated_fields`` attributes), subclass :class:`TranslatedModelAdmin`
instead;

.. code:: python

    from utils.translation import TranslatedModelAdmin

    class SomeItemAdmin(TranslatedModelAdmin):
        fields = (name, description)
"""

from django.conf import settings
from django.contrib import admin
from django.core.exceptions import FieldError, ImproperlyConfigured
from django.db import models
from django.db.models.fields.related import RelatedField
from django.utils.text import format_lazy
from django.utils.translation import get_language


class MultilingualField:
    """
    Transformed the passed-in form field into fields appended with the
    active languages and generates an automatic accessor property that
    translates based on the currently active language

    Requires a :class:`~django.db.models.Model` metaclassed by
    :class:`ModelTranslateMeta`.
    """

    def __init__(self, cls, *args, **kwargs):
        """Construct the MultilingualField

        :param cls: the form field to instantiate.
            Any additional arguments are passed to the field.
        """
        if issubclass(cls, RelatedField):
            # Especially naming the reverses gets quite messy for these.
            # TODO consider implementing this when there is a need for it.
            raise NotImplementedError("RelatedFields are not translatable.")
        if get_language() is None:
            raise ImproperlyConfigured("I18n does not appear to be activated.")
        self.cls = cls
        self.args = args
        self.kwargs = kwargs


def localize_attr_name(attr_name, language=None):
    """Generate the localized attribute name"""
    if language is None:
        language = get_language()
    if language is None:
        language = settings.LANGUAGE_CODE
    return "{}_{}".format(attr_name, language)


def _i18n_attr_accessor(attr):
    def _accessor(self):
        return getattr(self, localize_attr_name(attr))

    _accessor.__doc__ = "Accessor that fetches the localized " "variant of {}".format(
        attr
    )

    return _accessor


class ModelTranslateMeta(models.base.ModelBase):
    """Metaclass to handle the :class:`MultilingualField` transformations"""

    def __new__(mcs, name, bases, dct):
        field_i18n = {"default": {}, "fields": {}}
        try:
            # Inherit i18n fields from superclass
            field_i18n = bases[0]._meta._field_i18n
        except IndexError:
            pass
        except AttributeError:
            pass

        for attr, field in list(dct.items()):
            if not isinstance(field, MultilingualField):
                continue
            # ForeignKey, OneToOneField and ManyToManyField do not have
            # a verbose name as first positional argument.
            # But those are not translatable (see above).
            if field.args:
                verbose_base = ("args", field.args[0])
            else:
                verbose_base = ("kwargs", field.kwargs.get("verbose_name", attr))
            fields = []
            for lang in settings.LANGUAGES:
                attr_i18n = localize_attr_name(attr, lang[0])
                verbose_name = format_lazy("{} ({})", verbose_base[1], lang[0].upper())
                if verbose_base[0] == "args":
                    field.args = (verbose_name,) + field.args[1:]
                else:
                    field.kwargs["verbose_name"] = verbose_name
                if attr_i18n in dct:
                    raise FieldError(
                        "Explicit field {} is shadowed "
                        "by TranslateMeta.".format(attr_i18n)
                    )
                dct[attr_i18n] = field.cls(*field.args, **field.kwargs)
                fields.append(attr_i18n)
            dct[attr] = property(_i18n_attr_accessor(attr))
            default = localize_attr_name(attr, settings.LANGUAGE_CODE)
            if default not in dct:
                raise ImproperlyConfigured("LANGUAGE_CODE not in LANGUAGES.")
            field_i18n["default"][attr] = default
            field_i18n["fields"][attr] = fields
        model = super().__new__(mcs, name, bases, dct)
        if hasattr(model._meta, "_field_i18n"):
            raise FieldError("TranslateMeta map already exists!")
        model._meta._field_i18n = field_i18n

        return model


class TranslatedModelAdmin(admin.ModelAdmin):
    """
    This class should be used when :class:`~django.contrib.admin.ModelAdmin`
    is used with a translated model and one refers to such a field in the
    ``fields`` or ``fieldsets`` attributes, or in ``prepopulated_fields``.

    This works because :class:`~django.contrib.admin.ModelAdmin` has an empty
    metaclass; we can hook in to ``__init__`` and modify the attributes
    when ``model`` is known.
    """

    def __init__(self, model, admin_site):
        for key, fields in list(type(self).prepopulated_fields.items()):
            # Replace translated fields in `fields`
            fields = tuple(
                model._meta._field_i18n["default"].get(field, field) for field in fields
            )
            # ..and in `key`
            del type(self).prepopulated_fields[key]
            key = model._meta._field_i18n["default"].get(key, key)
            type(self).prepopulated_fields[key] = fields

        def _trans_fields(fields):
            if fields is None:
                return None
            fields = [
                model._meta._field_i18n["fields"].get(field, (field,))
                for field in fields
            ]
            return tuple(field for fieldset in fields for field in fieldset)

        # In fields, we replace a translated field by all resulting fields.
        type(self).fields = _trans_fields(type(self).fields)
        type(self).exclude = _trans_fields(type(self).exclude)
        type(self).search_fields = _trans_fields(type(self).search_fields)

        if type(self).fieldsets is not None:
            for fieldset in type(self).fieldsets:
                fieldset[1]["fields"] = _trans_fields(fieldset[1]["fields"])

        super().__init__(model, admin_site)
