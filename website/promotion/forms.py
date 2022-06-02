from django import forms
from django.utils import timezone

from promotion.models import PromotionRequest
from thaliawebsite.settings import PROMO_PUBLISH_DATE_TIMEDELTA


class PromotionRequestForm(forms.ModelForm):
    class Meta:
        model = PromotionRequest
        fields = [
            "event",
            "publish_date",
            "channel",
            "assigned_to",
            "status",
            "drive_folder",
            "remarks",
        ]

    def clean_publish_date(self):
        publish_date = self.cleaned_data.get("publish_date")
        create_time_minimum = publish_date - PROMO_PUBLISH_DATE_TIMEDELTA
        if timezone.localdate() > create_time_minimum:
            raise forms.ValidationError(
                "Publish date cannot be within a week from now."
            )
        if "publish_date" in self.changed_data:
            create_time_minimum = publish_date - PROMO_PUBLISH_DATE_TIMEDELTA
            if timezone.localdate() > create_time_minimum:
                raise forms.ValidationError(
                    "Publish date cannot be within a week from now."
                )
        return publish_date
