from django.contrib import admin
from django.contrib.admin import register

from events.models import BlacklistedEventsUser, EventRegistration, EventsUser


class EventRegistrationUserInline(admin.TabularInline):
    model = EventRegistration


@register(EventsUser)
class EventsUserAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    inlines = [EventRegistrationUserInline]


@register(BlacklistedEventsUser)
class BlacklistedEventsUserAdmin(admin.ModelAdmin):
    pass
