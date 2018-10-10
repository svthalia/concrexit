from django import template
from django.conf import settings
from django.templatetags.static import static
from django.utils.translation import ugettext_lazy as _

from members.templatetags.member_card import member_card
from thaliawebsite.templatetags.grid_item import grid_item
from utils.templatetags.thumbnail import thumbnail

register = template.Library()


@register.inclusion_tag('includes/grid_item.html')
def membergroup_card(group):
    image_url = static('activemembers/images/placeholder_overview.png')
    if group.photo:
        image_url = thumbnail(group.photo, settings.THUMBNAIL_SIZES['medium'])

    return grid_item(
        title=group.name,
        meta_text='',
        url=group.get_absolute_url,
        image_url=image_url,
        class_name='membergroup-card',
    )


@register.inclusion_tag('includes/grid_item.html')
def membergroup_member_card(membership):
    meta_text = ''
    if 'since' in membership:
        since_text = _('Committee member since: ') + '?'
        if membership['since'].year > 1970:
            since_text = _('Committee member since: {}').format(
                membership['since'].year)
        meta_text += '<p class="px-1">{}</p>'.format(since_text)
    if 'role' in membership and membership['role']:
        meta_text += '<p class="px-1">{}</p>'.format(membership['role'])
    ribbon = None
    if membership['chair']:
        ribbon = _('Chair')

    return member_card(
        member=membership['member'],
        meta_text=meta_text,
        ribbon=ribbon
    )
