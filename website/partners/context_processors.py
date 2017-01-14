from random import shuffle

from partners.models import Partner


def showcased_partners(request):
    if 'partner_sequence' not in request.session:
        partner_ids = [p.id for p in Partner.objects.filter(is_active=True)]
        shuffle(partner_ids)
        request.session['partner_sequence'] = partner_ids

    sequence = request.session['partner_sequence']
    chosen, rest = sequence[:2], sequence[2:]
    request.session['partner_sequence'] = rest + chosen

    try:
        partners = tuple(Partner.objects.get(id=id) for id in chosen)
    except Partner.DoesNotExist:
        del request.session['partner_sequence']
        return showcased_partners(request)

    return {'showcased_partners': partners}
