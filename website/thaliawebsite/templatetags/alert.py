from django import template

register = template.Library()


@register.inclusion_tag("includes/alert.html")
def alert(alert_type="info", message=None, dismissible=False, extra_classes=""):
    if dismissible:
        extra_classes += " alert-dismissible"
    return {
        "type": alert_type,
        "message": message,
        "dismissible": dismissible,
        "extra_classes": extra_classes,
    }
