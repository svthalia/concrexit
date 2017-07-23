from django import template

register = template.Library()


@register.inclusion_tag('registrations/form_field.html')
def form_field(form, field_name):
    return {'field': form.__getitem__(field_name)}
