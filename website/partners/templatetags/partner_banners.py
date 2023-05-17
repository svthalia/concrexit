from random import sample

from django import template

from partners.models import Partner
from utils.media.services import fetch_thumbnails_db

register = template.Library()


@register.inclusion_tag("partners/banners.html", takes_context=True)
def render_partner_banners(context):
    """Render the partner banner."""
    request = context["request"]
    all_partners = Partner.objects.filter(is_active=True).order_by("id")
    ids = [partner.id for partner in all_partners]

    # check if partners have changed; if so, update sequence in session
    if (
        "partner_sequence" not in request.session
        or "partner_ids" not in request.session
        or request.session["partner_ids"] != ids
    ):
        # Store a list of partner ids to allow checking for changes in partners
        request.session["partner_ids"] = ids
        request.session["partner_sequence"] = sample(ids, len(ids))

    sequence = request.session["partner_sequence"]
    chosen, rest = sequence[:4], sequence[4:]
    request.session["partner_sequence"] = rest + chosen

    partners = [p for p in all_partners if p.id in chosen]
    fetch_thumbnails_db(
        [p.alternate_logo or p.logo for p in partners],
        "medium",
    )

    return {
        "partners": partners,
        "thumb_size": "medium",
    }
