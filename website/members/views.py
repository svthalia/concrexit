from django.shortcuts import get_object_or_404, render
from django.utils.text import slugify

from . import models

import os
from sendfile import sendfile


def index(request):
    members = models.Member.objects.all()
    return render(request, 'members/index.html', {'members': members})


def become_a_member(request):
    context = {'documents': models.BecomeAMemberDocument.objects.all()}
    return render(request, 'singlepages/become_a_member.html', context)


def get_become_a_member_document(request, pk):
    document = get_object_or_404(models.BecomeAMemberDocument, pk=int(pk))
    _, ext = os.path.splitext(document.file.path)
    return sendfile(request, document.file.path, attachment=True,
                    attachment_filename=slugify(document.name) + ext)
