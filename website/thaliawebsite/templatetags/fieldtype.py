from django import template

register = template.Library()


@register.filter(name="fieldtype")
def fieldtype(field):
    """Get the field type for a form field.

    :param field: field for which to get the field type
    :return: field type
    :rtype: str
    """
    return field.field.widget.__class__.__name__
