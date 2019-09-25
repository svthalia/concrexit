from django import template

register = template.Library()


@register.inclusion_tag('includes/alert.html')
def alert(type='info', message=None, dismissible=False, extra_classes=''):
    if dismissible:
        extra_classes += ' alert-dimissable'
    return {
        'type': type,
        'message': message,
        'dismissible': dismissible,
        'extra_classes': extra_classes,
    }
