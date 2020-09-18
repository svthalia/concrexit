from django.shortcuts import get_object_or_404, render
from django.db.models import Max
from django.conf import settings
from django.http import JsonResponse

from .models import Thabloid


def index(request):
    """Render Thabloid overview index page."""
    thabloids = Thabloid.objects.all()
    context = {
        "thabloids": thabloids,
        "year": thabloids.aggregate(Max("year")).get("year__max"),
    }
    return render(request, "thabloid/index.html", context)


def pages(request, year, issue):
    """Return paths of individual Thabloid pages."""
    thabloid = get_object_or_404(Thabloid, year=int(year), issue=int(issue))
    files = [{"src": "{}{}".format(settings.MEDIA_URL, p)} for p in thabloid.pages]
    return JsonResponse(files, safe=False)
