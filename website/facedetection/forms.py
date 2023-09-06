from django import forms
from django.conf import settings

from .models import ReferenceFace


class ReferenceFaceUploadForm(forms.ModelForm):
    """Class for a reference face submission form."""

    class Meta:
        """Meta class for ReferenceFaceUploadForm."""

        model = ReferenceFace
        fields = ("file",)

    def save(self, commit=True, user=None):
        """Save the user encoding."""
        if not user:
            raise forms.ValidationError("User must be specified.")

        instance = super().save(commit=False)
        instance.user = user

        if (
            user.reference_faces.filter(
                marked_for_deletion_at__isnull=True,
            ).count()
            >= settings.FACEDETECTION_MAX_NUM_REFERENCE_FACES
        ):
            raise forms.ValidationError(
                "You have reached the maximum number of reference faces"
            )

        if commit:
            instance.save()
        return instance
