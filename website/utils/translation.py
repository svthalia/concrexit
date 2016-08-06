from django.db import models
from django.conf import settings


class MultilingualField(object):

    def __init__(self, cls, *args, **kwargs):
        self.cls = cls
        self.args = args
        self.kwargs = kwargs


class ModelTranslateMeta(models.base.ModelBase):

    def __new__(cls, name, bases, dct):
        for attr, field in list(dct.items()):
            if isinstance(field, MultilingualField):
                verbose_name_base = field.kwargs.get('verbose_name', None)
                for lang in settings.LANGUAGES:
                    attr_i18n = attr + '_' + lang[0]
                    if verbose_name_base is not None:
                        field.kwargs['verbose_name'] = '{} ({})'.format(
                                                            verbose_name_base,
                                                            lang[0].upper())
                    dct[attr_i18n] = field.cls(*field.args, **field.kwargs)
                del dct[attr]
        return super(ModelTranslateMeta, cls).__new__(cls, name, bases, dct)
