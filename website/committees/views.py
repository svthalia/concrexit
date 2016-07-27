from django.shortcuts import render, get_object_or_404

from .models import Committee


def index(request):
    """Overview of committees"""
    committees = Committee.objects.all()

    return render(request,
                  'committees/index.html',
                  {'committees': committees})


def details(request, committee_id):
    """View the details of a committee"""
    committee = get_object_or_404(Committee, pk=committee_id)

    return render(request, 'committee/details.html',
                  {'committee': committee})
