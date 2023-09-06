from django import forms
from django.apps import AppConfig
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class ThabloidConfig(AppConfig):
    """AppConfig for the Thabloid app."""

    name = "thabloid"
    verbose_name = _("Thabloid")

    def menu_items(self):
        return {
            "categories": [{"name": "members", "title": "For Members", "key": 2}],
            "items": [
                {
                    "category": "members",
                    "title": "Thabloid",
                    "url": reverse("thabloid:index"),
                    "key": 5,
                }
            ],
        }

    def user_profile_form_fields(self, instance=None):
        from thabloid.models import ThabloidUser
        from thabloid.services import update_thabloid_blacklist_for_user

        default_value = True
        if instance:
            default_value = ThabloidUser.objects.get(pk=instance.user.pk).wants_thabloid

        return {
            "receive_thabloid": forms.BooleanField(
                required=False,
                label="Receive thabloid",
                help_text="Receive printed Thabloid magazines",
                initial=default_value,
            )
        }, update_thabloid_blacklist_for_user
