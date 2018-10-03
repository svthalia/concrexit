from random import sample

from partners.models import Partner


def showcased_partners(request):
    """
    Generate a sequence of showcased partners (banners)

    For each user we generate a sequence of banners. This sequence
    is then stored for that user, because doing it randomly creates
    a feel of an artificial 'bias' towards certain partners. Doing
    it this way ensures that everyone gets an exactly fair number of
    views.
    """
    all_partners = Partner.objects.filter(is_active=True).order_by('id')
    ids = [partner.id for partner in all_partners]

    # check if partners have changed; if so, update sequence in session
    if ('partner_sequence' not in request.session or
            'partner_ids' not in request.session or
            request.session['partner_ids'] != ids):
        # Store a list of partner ids to allow checking for changes in partners
        request.session['partner_ids'] = ids
        request.session['partner_sequence'] = sample(ids, len(ids))

    sequence = request.session['partner_sequence']
    chosen, rest = sequence[:4], sequence[4:]
    request.session['partner_sequence'] = rest + chosen

    return {
        'showcased_partners': [p for p in all_partners if p.id in chosen],
    }
