from django.db.models import Max
from django.shortcuts import get_object_or_404, render

from .models import Thabloid


def index(request):
    thabloids = Thabloid.objects.all()
    context = {'thabloids': thabloids,
               'year': thabloids.aggregate(Max('year')).get('year__max')}
    return render(request, 'thabloid/index.html', context)


def viewer(request, year, issue):
    thabloid = get_object_or_404(Thabloid, year=int(year), issue=int(issue))
    return render(request, 'thabloid/viewer.html', {'thabloid': thabloid})
