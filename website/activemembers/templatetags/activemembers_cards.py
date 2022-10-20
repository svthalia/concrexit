from django import template
from django.conf import settings
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _

from members.templatetags.member_card import member_card
from thaliawebsite.templatetags.grid_item import grid_item
from utils.media.services import get_thumbnail_url

register = template.Library()


@register.inclusion_tag("includes/grid_item.html")
def membergroup_card(group):
    image_url = static("activemembers/images/placeholder_overview.png")
    if group.photo:
        image_url = get_thumbnail_url(group.photo, settings.THUMBNAIL_SIZES["medium"])

    return grid_item(
        title=group.name,
        meta_text="",
        url=group.get_absolute_url,
        image_url=image_url,
        class_name="membergroup-card",
    )


@register.inclusion_tag("includes/grid_item.html")
def membergroup_member_card(membership):
    meta_text = ""

    if "role" in membership and membership["role"]:
        meta_text += f"<p class=\"px-1\">{membership['role']}</p>"

    ribbon = None
    if membership["chair"] and not membership["until"]:
        ribbon = _("Chair")

    if "since" in membership and not membership["is_board"]:
        since_text = "Member since: ?"
        if membership["since"].year > 1970:
            since_text = f"Member since: {membership['since'].year}"
        meta_text += f'<p class="px-1"><em>{since_text}</em></p>'

    if "until" in membership and membership["until"] and membership["is_board"]:
        until_text = f"until {membership['until']}"
        meta_text += f'<p class="px-1"><em>{until_text}</em></p>'

    return member_card(member=membership["member"], meta_text=meta_text, ribbon=ribbon)
