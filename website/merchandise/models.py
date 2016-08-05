from django.db import models


class MerchandiseItem(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=5, decimal_places=2)
    description = models.TextField()
    image = models.ImageField(upload_to='public/merchandise')

    def __str__(self):
        return self.name
