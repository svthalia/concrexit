from django.contrib import admin
from django.shortcuts import redirect

from utils.translation import TranslatedModelAdmin

from newsletters.models import (
    Newsletter,
    NewsletterEvent,
    NewsletterItem
)


class NewsletterItemInline(admin.StackedInline):
    model = NewsletterItem


class NewsletterEventInline(admin.StackedInline):
    model = NewsletterEvent


@admin.register(Newsletter)
class NewsletterAdmin(TranslatedModelAdmin):
    list_display = ('title', 'date', 'sent',)
    inlines = (NewsletterItemInline, NewsletterEventInline,)

    fieldsets = (
        (None, {
            'fields': (
                'title', 'date', 'description'
            )
        }),
    )

    def change_view(self, request, object_id, form_url=''):
        obj = Newsletter.objects.filter(id=object_id)[0]
        if obj is not None and obj.sent is True:
            return redirect(obj)
        return super(NewsletterAdmin, self).change_view(
            request, object_id, form_url, {'newsletter': obj})

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.sent is True:
            return False
        return (super(NewsletterAdmin, self)
                .has_delete_permission(request, obj=obj))

    def get_actions(self, request):
        actions = super(NewsletterAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions
