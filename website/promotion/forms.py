from django import forms
from django.utils import timezone

from promotion.models import PromotionRequest


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

    def clean(self):
        cleaned_data = super().clean()
        if "publish_date" in self.changed_data and "channel" in self.cleaned_data:
            publish_date = cleaned_data.get("publish_date")
            minimum_delta = cleaned_data.get("channel").publish_deadline
            create_time_minimum = publish_date - minimum_delta
            if timezone.localdate() > create_time_minimum:
                raise forms.ValidationError(
                    f"Publish date cannot be within {minimum_delta.days} days from now for this channel."
                )
        return cleaned_data
