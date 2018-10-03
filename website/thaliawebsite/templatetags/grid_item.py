from django import template

register = template.Library()


@register.inclusion_tag('includes/grid_item.html')
def grid_item(title=None, meta_text=None, url=None, image_url=None, ribbon=None, class_name=''):
    return {
        'title': title,
        'url': url,
        'image_url': image_url,
        'meta_text': meta_text,
        'ribbon': ribbon,
        'class_name': class_name
    }
