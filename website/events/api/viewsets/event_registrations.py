from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from events import services
from events.api.serializers import EventRegistrationSerializer
from events.exceptions import RegistrationError
from events.models import EventRegistration
from payments.exceptions import PaymentError


class EventRegistrationViewSet(GenericViewSet, RetrieveModelMixin, UpdateModelMixin):
    """
    Defines the viewset for registrations, requires an authenticated user.
    Has custom update and destroy methods that use the services.
    """

    queryset = EventRegistration.objects.all()
    serializer_class = EventRegistrationSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def get_object(self):
        instance = super().get_object()
        if (
            instance.name or instance.member.pk != self.request.member.pk
        ) and not services.is_organiser(self.request.member, instance.event):
            raise NotFound()

        return instance

    # Always set instance so that OPTIONS call will show the info fields too
    def get_serializer(self, *args, **kwargs):
        if len(args) == 0 and "instance" not in kwargs:
            kwargs["instance"] = self.get_object()
        return super().get_serializer(*args, **kwargs)

    def perform_update(self, serializer):
        try:
            registration = serializer.instance

            member = self.request.member
            if (
                member
                and member.has_perm("events.change_registration")
                and services.is_organiser(member, registration.event)
            ):
                services.update_registration_by_organiser(
                    registration, self.request.member, serializer.validated_data
                )

            services.update_registration(
                registration=registration, field_values=serializer.field_values()
            )
            serializer.information_fields = services.registration_fields(
                serializer.context["request"], registration=registration
            )
        except RegistrationError as e:
            raise PermissionDenied(detail=e) from e
        except PaymentError as e:
            raise PermissionDenied(detail=e) from e

    def destroy(self, request, pk=None, **kwargs):
        registration = self.get_object()
        try:
            services.cancel_registration(registration.member, registration.event)
            return Response(status=204)
        except RegistrationError as e:
            raise PermissionDenied(detail=e) from e
