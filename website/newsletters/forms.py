from django import forms
from django.utils.translation import ugettext_lazy as _

from .models import NewsletterItem, NewsletterEvent


class NewsletterEventForm(forms.ModelForm):
    order = forms.IntegerField(label=_('order'), initial=0)

    class Meta:
        fields = '__all__'
        model = NewsletterEvent


class NewsletterItemForm(forms.ModelForm):
    order = forms.IntegerField(label=_('order'), initial=0)

    class Meta:
        fields = '__all__'
        model = NewsletterItem
