from django import forms
from django.utils.translation import gettext_lazy as _

from events.models import Event
from sales.models.product import ProductListItem
from sales.models.shift import Shift


class ProductItemField(forms.IntegerField):
    def get_productlistitem(self):
        return self._productlistitem

    def get_product(self):
        return self._productlistitem.product

    def set_productlistitem(self, product_list_item):
        self._productlistitem = product_list_item


class ProductOrderForm(forms.Form):
    def __init__(self, product_list, is_adult, *args, **kwargs):
        super().__init__(*args, **kwargs)
        product_list_items = ProductListItem.objects.filter(product_list=product_list)
        for item in product_list_items:
            field = ProductItemField(
                label=item.product.name,
                required=False,
                min_value=0,
            )
            field.set_productlistitem(item)
            if not is_adult and item.product.age_restricted:
                field.disabled = True
            self.fields[f"product_{item.product.pk}"] = field


class ShiftAdminForm(forms.ModelForm):
    """Require every shift to be linked to an event, or to explicitly have no event."""

    NO_EVENT = "no-event"

    event = forms.ChoiceField(
        label=_("linked event"),
        help_text=_(
            "Sales of a shift without an event are pushed to Moneybird without a "
            "project, so the treasurer can assign one."
        ),
    )

    class Meta:
        model = Shift
        # no_event is set from the event choice in clean_event().
        exclude = ("no_event",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["event"].choices = [
            ("", "---------"),
            (self.NO_EVENT, _("No event")),
            *((event.pk, str(event)) for event in Event.objects.all()),
        ]
        if self.instance.pk is not None:
            if self.instance.event_id is not None:
                self.initial["event"] = self.instance.event_id
            elif self.instance.no_event:
                self.initial["event"] = self.NO_EVENT

    def clean_event(self):
        value = self.cleaned_data["event"]
        self.instance.no_event = value == self.NO_EVENT
        if self.instance.no_event:
            return None
        return Event.objects.get(pk=value)
