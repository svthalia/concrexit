from django import template

register = template.Library()


@register.inclusion_tag('includes/alert.html')
def alert(type='info', message=None, dismissable=False, extra_classes=''):
    if dismissable:
        extra_classes += ' alert-dimissable'
    return {
        'type': type,
        'message': message,
        'dismissable': dismissable,
        'extra_classes': extra_classes,
    }
