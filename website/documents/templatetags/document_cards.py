from django import template
from django.templatetags.static import static

from documents.models import AnnualDocument
from thaliawebsite.templatetags.grid_item import grid_item

register = template.Library()


@register.inclusion_tag("includes/grid_item.html")
def association_document_card(document):
    return grid_item(
        title=document.name,
        meta_text="",
        url=document.get_absolute_url(),
        image_url=static("documents/images/thumb.png"),
        class_name="association-document-card",
    )


@register.inclusion_tag("includes/grid_item.html")
def event_document_card(document):
    return grid_item(
        title=document.name,
        meta_text="",
        url=document.get_absolute_url(),
        image_url=static("documents/images/thumb.png"),
        class_name="event-document-card",
    )


@register.inclusion_tag("includes/grid_item.html")
def annual_document_card(doc_type, document):
    name = ""
    class_name = "annual-document-card"
    for t, n in AnnualDocument.SUBCATEGORIES:
        if t == doc_type:
            name = n
    url = f"#{doc_type}"

    if document:
        url = document.get_absolute_url()
        image_url = static("documents/images/thumb.png")
    else:
        class_name += " empty"
        image_url = static("documents/images/placeholder.png")

    return grid_item(
        title=name,
        meta_text="",
        url=url,
        image_url=image_url,
        class_name=class_name,
    )
