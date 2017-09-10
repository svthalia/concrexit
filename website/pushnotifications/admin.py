from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from pushnotifications import models
from pushnotifications.models import Message


@admin.register(models.Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'active', 'date_created')
    list_filter = ('active', 'type')
    actions = ('enable', 'disable')

    search_fields = ('name', 'device_id', 'user__username')

    def enable(self, request, queryset):
        queryset.update(active=True)

    enable.short_description = _('Enable selected devices')

    def disable(self, request, queryset):
        queryset.update(active=False)

    disable.short_description = _('Disable selected devices')


@admin.register(models.Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('title', 'body', 'sent', 'success', 'failure')
    filter_horizontal = ('users',)
    list_filter = ('sent',)

    def get_fields(self, request, obj=None):
        if obj and obj.sent:
            return 'users', 'title', 'body', 'success', 'failure'
        return 'users', 'title', 'body'

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.sent:
            return 'users', 'title', 'body', 'success', 'failure'
        return super().get_readonly_fields(request, obj)

    def change_view(self, request, object_id, form_url='', **kwargs):
        obj = Message.objects.filter(id=object_id)[0]
        return super(MessageAdmin, self).change_view(
            request, object_id, form_url, {'message': obj})
