from django.shortcuts import get_object_or_404, render
from django.db.models import Max
from django.conf import settings
from django.http import JsonResponse

from .models import Thabloid


def index(request):
    thabloids = Thabloid.objects.all()
    context = {'thabloids': thabloids,
               'year': thabloids.aggregate(Max('year')).get('year__max')}
    return render(request, 'thabloid/index.html', context)


def pages(request, year, issue):
    thabloid = get_object_or_404(Thabloid, year=int(year), issue=int(issue))
    pages = ['{}{}'.format(settings.MEDIA_URL, p) for p in thabloid.pages]
    return JsonResponse(pages, safe=False)
