from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from facerecognition.forms import ReferenceFaceUploadForm
from photos.models import Photo


@login_required
def your_photos(request):
    photos = Photo.objects.filter(
        face_recognition_photo__encodings__matches__member__exact=request.member,
        album__hidden=False,
    )
    context = {
        "photos": photos,
        "has_unprocessed_reference_faces": request.member.reference_faces.filter(
            encoding__isnull=True
        ).exists(),
        "has_reference_faces": request.member.reference_faces.exists(),
    }
    return render(request, "facerecognition/your-photos.html", context)


class ReferenceFaceUploadView(FormView):
    template_name = "facerecognition/reference-face-upload.html"
    form_class = ReferenceFaceUploadForm
    success_url = reverse_lazy("photos:facerecognition:your-photos")

    def form_valid(self, form):
        form.save(self.request.member)
        messages.success(self.request, _("Your reference face has been uploaded."))
        return super().form_valid(form)
