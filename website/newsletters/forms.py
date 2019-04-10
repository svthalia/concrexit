"""The forms defined by the newsletters package"""
from django import forms
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from events.models import Event
from .models import NewsletterItem, NewsletterEvent, Newsletter


class NewsletterItemForm(forms.ModelForm):
    """Custom ModelForm for the NewsletterItem model to add the order field"""
    order = forms.IntegerField(label=_('order'), initial=0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            newsletter = self.instance.newsletter
            order = newsletter.get_newslettercontent_order()
            order_value = list(order).index(self.instance.pk)
            self.fields['order'].initial = order_value
        except Newsletter.DoesNotExist:
            pass

    class Meta:
        fields = '__all__'
        model = NewsletterItem


class NewsletterEventForm(NewsletterItemForm):
    """
    Custom ModelForm for the NewsletterEvent model to
    add the order field and javascript for automatic field filling
    """
    event = forms.ChoiceField(
        label=_('Event')
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['event'].choices = [(None, '-----')] + [
            (e.pk, e.title_nl) for e in
            Event.objects.filter(published=True, start__gt=timezone.now())
        ]
        self.fields['event'].required = False

    class Meta:
        fields = ('event', 'title_en', 'title_nl',
                  'description_en', 'description_nl', 'what_en', 'what_nl',
                  'where_en', 'where_nl', 'start_datetime', 'end_datetime',
                  'show_costs_warning', 'price', 'penalty_costs')
        model = NewsletterEvent

    class Media:
        js = (
            'js/js.cookie.min.js',
            'admin/newsletters/js/forms.js',
        )
