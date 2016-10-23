from django.conf import settings
from django.contrib import admin
from django.core.exceptions import FieldError, ImproperlyConfigured
from django.db import models
from django.db.models.fields.related import RelatedField
from django.utils.translation import get_language, string_concat

"""This module makes it easy to define translatable model fields.

To use it in a models.py, make sure you;
  - set the metaclass of your model to ModelTranslateMeta
  - replace any translatable model fields by MultilingualField instances
  - make and apply database migrations

See the following usage example;

    from django.db import models
    from utils.translation import MultilingualField, ModelTranslateMeta

    class SomeItem(models.Model, metaclass=ModelTranslateMeta):

        name = MultilingualField(models.CharField, max_length=100)
        description = MultilingualField(models.TextField)

In order to use the fields in ModelAdmin configuration (such as in the
fields, fieldsets or prepopulated_fields attributes), subclass the Admin object
from TranslatedModelAdmin instead;

    from utils.translation import TranslatedModelAdmin

    class SomeItemAdmin(TranslatedModelAdmin):
        fields = (name, description)
"""


I18N_FIELD_FORMAT = '{}_{}'


class MultilingualField(object):

    def __init__(self, cls, *args, **kwargs):
        if issubclass(cls, RelatedField):
            # Especially naming the reverses gets quite messy for these.
            # TODO consider implementing this when there is a need for it.
            raise NotImplementedError("RelatedFields are not translatable.")
        if get_language() is None:
            raise ImproperlyConfigured("I18n does not appear to be activated.")
        self.cls = cls
        self.args = args
        self.kwargs = kwargs


def _i18n_attr_accessor(attr, lang):

    def accessor(self):
        return getattr(self, I18N_FIELD_FORMAT.format(attr, lang))

    return accessor


class ModelTranslateMeta(models.base.ModelBase):

    def __new__(cls, name, bases, dct):
        field_i18n = {'default': {}, 'fields': {}}
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
            if len(field.args) > 0:
                verbose_base = ('args', field.args[0])
            else:
                verbose_base = ('kwargs', field.kwargs.get('verbose_name',
                                                           attr))
            fields = []
            for lang in settings.LANGUAGES:
                attr_i18n = I18N_FIELD_FORMAT.format(attr, lang[0])
                verbose_name = string_concat(
                    verbose_base[1], ' (', lang[0].upper(), ')')
                if verbose_base[0] == 'args':
                    field.args = (verbose_name,) + field.args[1:]
                else:
                    field.kwargs['verbose_name'] = verbose_name
                if attr_i18n in dct:
                    raise FieldError("Explicit field {} is shadowed "
                                     "by TranslateMeta.".format(attr_i18n))
                dct[attr_i18n] = field.cls(*field.args, **field.kwargs)
                fields.append(attr_i18n)
            dct[attr] = property(_i18n_attr_accessor(attr, get_language()))
            default = I18N_FIELD_FORMAT.format(attr, settings.LANGUAGE_CODE)
            if default not in dct:
                raise ImproperlyConfigured("LANGUAGE_CODE not in LANGUAGES.")
            field_i18n['default'][attr] = default
            field_i18n['fields'][attr] = fields
        model = super(ModelTranslateMeta, cls).__new__(cls, name, bases, dct)
        if hasattr(model._meta, '_field_i18n'):
            raise FieldError("TranslateMeta map already exists!")
        model._meta._field_i18n = field_i18n
        return model


class TranslatedModelAdmin(admin.ModelAdmin):
    """This class should be used when the ModelAdmin is used with a
    translated model and one refers to such a field in the `fields`
    or `fieldsets` attributes, or in `prepopulated_fields`.

    This works because admin.ModelAdmin has an empty metaclass; we can hook
    in to __init__ and modify the attributes when model is known."""

    def __init__(self, model, admin_site):
        for key, fields in list(type(self).prepopulated_fields.items()):
            # Replace translated fields in `fields`
            fields = tuple(model._meta._field_i18n['default'].get(field, field)
                           for field in fields)
            # ..and in `key`
            del type(self).prepopulated_fields[key]
            key = model._meta._field_i18n['default'].get(key, key)
            type(self).prepopulated_fields[key] = fields

        def trans_fields(fields):
            if fields is None:
                return None
            fields = [model._meta._field_i18n['fields']
                      .get(field, (field, )) for field in fields]
            return tuple(field for fieldset in fields for field in fieldset)

        # In fields, we replace a translated field by all resulting fields.
        type(self).fields = trans_fields(type(self).fields)
        type(self).exclude = trans_fields(type(self).exclude)
        type(self).search_fields = trans_fields(type(self).search_fields)

        if type(self).fieldsets is not None:
            for fieldset in type(self).fieldsets:
                fieldset[1]['fields'] = trans_fields(fieldset[1]['fields'])

        super(TranslatedModelAdmin, self).__init__(model, admin_site)
