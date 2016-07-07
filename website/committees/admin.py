from django.contrib import admin

from . import models

admin.site.register(models.Committee)
admin.site.register(models.CommitteeMembership)
# Register your models here.
