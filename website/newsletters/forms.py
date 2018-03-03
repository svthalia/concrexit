"""The forms defined by the newsletters package"""
from django import forms
from django.utils.translation import ugettext_lazy as _

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
    """Custom ModelForm for the NewsletterEvent model to add the order field"""
    class Meta:
        fields = '__all__'
        model = NewsletterEvent
