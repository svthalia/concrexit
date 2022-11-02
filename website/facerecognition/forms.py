from django import forms

from facerecognition.models import ReferenceFace


class ReferenceFaceUploadForm(forms.ModelForm):
    """Class for a reference face submission form."""

    class Meta:
        """Meta class for ReferenceFaceUploadForm."""

        model = ReferenceFace
        fields = ("file",)

    def save(self, member=None, commit=True):
        """Save the user encoding."""
        if not member:
            raise forms.ValidationError("Member must be specified")
        instance = super().save(commit=False)
        instance.member = member
        if commit:
            instance.save()
        return instance
