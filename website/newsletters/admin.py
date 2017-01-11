from django.contrib import admin
from django.shortcuts import redirect

from newsletters.models import Newsletter, NewsletterEvent, NewsletterItem
from utils.translation import TranslatedModelAdmin

from .forms import NewsletterEventForm, NewsletterItemForm


class NewsletterItemInline(admin.StackedInline):
    form = NewsletterItemForm
    model = NewsletterItem
    extra = 0
    ordering = ('_order',)


class NewsletterEventInline(admin.StackedInline):
    form = NewsletterEventForm
    model = NewsletterEvent
    extra = 0
    ordering = ('_order',)


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

    def save_formset(self, request, form, formset, change):
        """Save formsets with their order"""
        formset.save()

        form.instance.set_newslettercontent_order([
            f.instance.pk
            for f in sorted(formset.forms,
                            key=lambda x: (x.cleaned_data['order'],
                                           x.instance.pk))
        ])
        form.instance.save()

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
