from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import DeleteView, FormView, ListView

from photos.models import Photo
from thaliawebsite.views import PagedView

from .forms import ReferenceFaceUploadForm
from .models import ReferenceFace


class YourPhotosView(LoginRequiredMixin, PagedView):
    model = Photo
    paginate_by = 50
    template_name = "facedetection/your-photos.html"
    context_object_name = "photos"

    def get(self, request, *args, **kwargs):
        if not request.member or request.member.current_membership is None:
            messages.error(request, _("You need to be a member to use this feature."))
            return redirect("index")

        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        member = self.request.member

        reference_faces = member.reference_faces.filter(
            marked_for_deletion_at__isnull=True,
        )

        # Filter out matches from long before the member's first membership.
        albums_since = member.earliest_membership.since - timezone.timedelta(days=31)
        photos = Photo.objects.select_related("album").filter(
            album__date__gte=albums_since
        )

        # Filter out matches from after the member's last membership.
        if member.latest_membership.until is not None:
            photos = photos.filter(album__date__lte=member.latest_membership.until)

        # Actually match the reference faces.
        photos = photos.filter(album__hidden=False, hidden=False).filter(
            facedetectionphoto__encodings__matches__reference__in=reference_faces,
        )

        return photos.select_properties("num_likes").order_by("-album__date", "-pk")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context[
            "has_processing_reference_faces"
        ] = self.request.member.reference_faces.filter(
            status=ReferenceFace.Status.PROCESSING,
            marked_for_deletion_at__isnull=True,
        ).exists()

        context[
            "has_rejected_reference_faces"
        ] = self.request.member.reference_faces.filter(
            status=ReferenceFace.Status.REJECTED,
            marked_for_deletion_at__isnull=True,
        ).exists()

        context["has_reference_faces"] = self.request.member.reference_faces.filter(
            marked_for_deletion_at__isnull=True
        ).exists()

        return context


class ReferenceFaceView(LoginRequiredMixin, ListView):
    template_name = "facedetection/reference-faces.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[
            "reference_faces_limit"
        ] = settings.FACEDETECTION_MAX_NUM_REFERENCE_FACES
        context[
            "storage_period_after_delete"
        ] = settings.FACEDETECTION_REFERENCE_FACE_STORAGE_PERIOD_AFTER_DELETE_DAYS
        context["reference_faces_limit_reached"] = bool(
            self.request.member.reference_faces.filter(
                marked_for_deletion_at__isnull=True
            ).count()
            >= settings.FACEDETECTION_MAX_NUM_REFERENCE_FACES
        )
        context[
            "has_rejected_reference_faces"
        ] = self.request.member.reference_faces.filter(
            status=ReferenceFace.Status.REJECTED,
            marked_for_deletion_at__isnull=True,
        ).exists()
        return context

    def get_queryset(self):
        return self.request.member.reference_faces.filter(
            marked_for_deletion_at__isnull=True
        ).all()


class ReferenceFaceUploadView(LoginRequiredMixin, FormView):
    template_name = "facedetection/reference-face-upload.html"
    form_class = ReferenceFaceUploadForm
    success_url = reverse_lazy("facedetection:reference-faces")

    def dispatch(self, request, *args, **kwargs):
        if not request.member or request.member.current_membership is None:
            messages.error(request, "You need to be a member to use this feature.")
            return redirect("index")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            form.save(user=self.request.member)
        except ValidationError as e:
            for error in e:
                messages.error(self.request, error)
            return self.form_invalid(form)
        messages.success(self.request, "Your reference face has been uploaded.")
        return super().form_valid(form)


class ReferenceFaceDeleteView(LoginRequiredMixin, DeleteView):
    model = ReferenceFace
    success_url = reverse_lazy("facedetection:reference-faces")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[
            "storage_period_after_delete"
        ] = settings.FACEDETECTION_REFERENCE_FACE_STORAGE_PERIOD_AFTER_DELETE_DAYS
        return context

    def get_queryset(self):
        return self.request.member.reference_faces.filter(
            marked_for_deletion_at__isnull=True
        ).all()

    def form_valid(self, form):
        success_url = self.get_success_url()

        instance = self.get_object()
        instance.marked_for_deletion_at = timezone.now()
        instance.save()
        messages.success(self.request, "Your reference face has been deleted.")

        return HttpResponseRedirect(success_url)
