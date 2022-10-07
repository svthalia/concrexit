from django import template
from django.conf import settings
from django.templatetags.static import static
from django.urls import reverse

from thaliawebsite.templatetags.grid_item import grid_item
from utils.media.services import get_thumbnail_url

register = template.Library()


@register.inclusion_tag("includes/grid_item.html")
def member_card(member, meta_text=None, ribbon=None):
    if meta_text is None and member.profile.starting_year:
        meta_text = f'<p class="px-1">Cohort: {member.profile.starting_year}</p>'

    image_url = static("members/images/default-avatar.jpg")
    if member.profile.photo:
        image_url = get_thumbnail_url(
            member.profile.photo, settings.THUMBNAIL_SIZES["medium"]
        )

    return grid_item(
        title=member.profile.display_name(),
        meta_text=meta_text,
        url=reverse("members:profile", kwargs={"pk": member.pk}),
        image_url=image_url,
        ribbon=ribbon,
        class_name="member-card",
    )
