from django.contrib.auth.decorators import login_required
from django.db.models import Max
from django.shortcuts import get_object_or_404, redirect, render

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
def thabloid(request, year, issue):
    """Redirect to the Thabloid file."""
    thabloid = get_object_or_404(Thabloid, year=year, issue=issue)
    return redirect(get_media_url(thabloid.file))
