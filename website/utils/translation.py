from django.db import models
from django.db.models.fields.related import RelatedField
from django.conf import settings
from django.utils.translation import get_language
from django.core.exceptions import ImproperlyConfigured


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


def _i18n_attr_accessor(attr):

    def accessor(self):
        return getattr(self, I18N_FIELD_FORMAT.format(attr, get_language()))

    return accessor


class ModelTranslateMeta(models.base.ModelBase):

    def __new__(cls, name, bases, dct):
        for attr, field in list(dct.items()):
            if isinstance(field, MultilingualField):
                # ForeignKey, OneToOneField and ManyToManyField do not have
                # a verbose name as first positional argument.
                # But those are not translatable (see above).
                if len(field.args) > 0:
                    verbose_base = ('args', field.args[0])
                else:
                    verbose_base = ('kwargs', field.kwargs.get('verbose_name',
                                                               None))
                for lang in settings.LANGUAGES:
                    attr_i18n = I18N_FIELD_FORMAT.format(attr, lang[0])
                    if verbose_base is not None:
                        verbose_name = '{} ({})'.format(verbose_base[1],
                                                        lang[0].upper())
                        if verbose_base[0] == 'args':
                            field.args = (verbose_name,) + field.args[1:]
                        else:
                            field.kwargs['verbose_name'] = verbose_name
                    dct[attr_i18n] = field.cls(*field.args, **field.kwargs)
                dct[attr] = property(_i18n_attr_accessor(attr))
        return super(ModelTranslateMeta, cls).__new__(cls, name, bases, dct)
