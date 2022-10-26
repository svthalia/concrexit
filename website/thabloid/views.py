from django.contrib.auth.decorators import login_required
from django.db.models import Max
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from utils.media.services import get_media_url

from .models import Thabloid


@login_required
def index(request):
    """Render Thabloid overview index page."""
    thabloids = Thabloid.objects.all()
    context = {
        "thabloids": thabloids,
        "year": thabloids.aggregate(Max("year")).get("year__max"),
    }
    return render(request, "thabloid/index.html", context)


@login_required
def pages(request, year, issue):
    """Return paths of individual Thabloid pages."""
    thabloid = get_object_or_404(Thabloid, year=int(year), issue=int(issue))
    files = [{"src": get_media_url(p)} for p in thabloid.pages]
    return JsonResponse(files, safe=False)
