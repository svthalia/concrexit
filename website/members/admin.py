"""
This module registers admin pages for the models
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from . import models


class MemberInline(admin.StackedInline):
    model = models.Member
    can_delete = False


class UserAdmin(BaseUserAdmin):
    inlines = (MemberInline,)
    # FIXME include proper filter for expiration
    # https://docs.djangoproject.com/en/1.9/ref/contrib/admin/#django.contrib.admin.ModelAdmin.list_filter
    list_filter = ('member__type',
                   'member__membership_expiration',
                   'is_superuser')
    # FIXME use nicer form
    # form = forms.AdminForm (base on ModelForm, reorder elements, etc).

admin.site.register(models.BecomeAMemberDocument)

# re-register User admin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
