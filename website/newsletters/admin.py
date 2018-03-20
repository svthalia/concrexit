"""Registers admin interfaces for the newsletters module"""
from django.contrib import admin
from django.shortcuts import redirect

from newsletters.models import Newsletter, NewsletterEvent, NewsletterItem
from utils.translation import TranslatedModelAdmin

from .forms import NewsletterEventForm, NewsletterItemForm


class NewsletterItemInline(admin.StackedInline):
    """The inline for the text items in the newsletter"""
    form = NewsletterItemForm
    model = NewsletterItem
    extra = 0
    ordering = ('_order',)

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        if obj is not None:
            count = obj.newslettercontent_set.count()
            formset.form.declared_fields['order'].initial = count
        return formset


class NewsletterEventInline(NewsletterItemInline):
    """The inline for the event items in the newsletter"""
    form = NewsletterEventForm
    model = NewsletterEvent


@admin.register(Newsletter)
class NewsletterAdmin(TranslatedModelAdmin):
    """Manage the newsletters"""
    #: available fields in the admin overview list
    list_display = ('title', 'date', 'sent',)
    #: available inlines in the admin change form
    inlines = (NewsletterItemInline, NewsletterEventInline,)
    #: available fieldsets in the admin change form
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
        """
        Renders the change view
        Disallow change access if a newsletter is marked as sent
        """
        obj = Newsletter.objects.filter(id=object_id)[0]
        if obj is not None and obj.sent is True:
            return redirect(obj)
        return super(NewsletterAdmin, self).change_view(
            request, object_id, form_url, {'newsletter': obj})

    def has_delete_permission(self, request, obj=None):
        """
        Check if delete permission is granted
        Disallow deletion if a newsletter is marked as sent
        """
        if obj is not None and obj.sent is True:
            return False
        return (super(NewsletterAdmin, self)
                .has_delete_permission(request, obj=obj))

    def get_actions(self, request):
        """Remove the deletion action from the admin"""
        actions = super(NewsletterAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions
