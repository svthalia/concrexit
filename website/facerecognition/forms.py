from django import forms
from django.conf import settings

from facerecognition.models import ReferenceFace


class ReferenceFaceUploadForm(forms.ModelForm):
    """Class for a reference face submission form."""

    class Meta:
        """Meta class for ReferenceFaceUploadForm."""

        model = ReferenceFace
        fields = ("file",)

    def save(self, commit=True, member=None):
        """Save the user encoding."""
        if not member:
            raise forms.ValidationError("Member must be specified")
        instance = super().save(commit=False)
        instance.member = member
        if (
            member.reference_faces.count()
            >= settings.FACE_DETECTION_MAX_NUM_REFERENCE_FACES
        ):
            raise forms.ValidationError(
                "You have reached the maximum number of reference faces"
            )
        if commit:
            instance.save()
        return instance
