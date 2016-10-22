from django.db import models

from utils.translation import ModelTranslateMeta, MultilingualField


class MerchandiseItem(models.Model, metaclass=ModelTranslateMeta):
    name = MultilingualField(models.CharField, max_length=200)
    price = models.DecimalField(max_digits=5, decimal_places=2)
    description = MultilingualField(models.TextField)
    image = models.ImageField(upload_to='public/merchandise')

    def __str__(self):
        return self.name
