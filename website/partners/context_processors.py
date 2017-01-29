from random import sample

from partners.models import Partner


def showcased_partners(request):
    all_partners = Partner.objects.filter(is_active=True).order_by('id')
    ids = [partner.id for partner in all_partners]

    # check if partners have changed; if so, update sequence in session
    if ('partner_sequence' not in request.session or
            'partner_ids' not in request.session or
            request.session['partner_ids'] != ids):
        request.session['partner_ids'] = ids
        request.session['partner_sequence'] = sample(ids, len(ids))

    sequence = request.session['partner_sequence']
    chosen, rest = sequence[:2], sequence[2:]
    request.session['partner_sequence'] = rest + chosen

    try:
        partners = tuple(p for p in all_partners if p.id in chosen)
    except Partner.DoesNotExist:
        del request.session['partner_sequence']
        return showcased_partners(request)

    return {'showcased_partners': partners}
