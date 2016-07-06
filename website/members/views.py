from django.shortcuts import render

from . import models


def index(request):
    members = models.Member.objects.all()
    return render(request, 'members/index.html', {'members': members})
