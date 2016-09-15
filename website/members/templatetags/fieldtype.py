from django import template

register = template.Library()


@register.filter(name='fieldtype')
def fieldtype(field):
    return field.field.widget.__class__.__name__
