from django.conf import settings
from django.templatetags.static import static
from rest_framework import serializers
from rest_framework.fields import empty

from events import services
from events.exceptions import RegistrationError
from events.models import EventRegistration, RegistrationInformationField
from payments.api.v1.fields import PaymentTypeField
from payments.models import Payment
from thaliawebsite.api.services import create_image_thumbnail_dict
from thaliawebsite.api.v1.cleaned_model_serializer import CleanedModelSerializer


class EventRegistrationListSerializer(CleanedModelSerializer):
    """Custom registration list serializer."""

    class Meta:
        model = EventRegistration
        fields = ("pk", "member", "name", "avatar")

    name = serializers.SerializerMethodField("_name")
    avatar = serializers.SerializerMethodField("_avatar")
    member = serializers.SerializerMethodField("_member")

    def _member(self, instance):
        if instance.member:
            return instance.member.pk
        return None

    def _name(self, instance):
        if instance.member:
            return instance.member.profile.display_name()
        return instance.name

    def _avatar(self, instance):
        placeholder = self.context["request"].build_absolute_uri(
            static("members/images/default-avatar.jpg")
        )
        file = None
        if instance.member and instance.member.profile.photo:
            file = instance.member.profile.photo
        return create_image_thumbnail_dict(
            self.context["request"], file, placeholder=placeholder, size_large="800x800"
        )


class EventRegistrationAdminListSerializer(EventRegistrationListSerializer):
    """Custom registration admin list serializer."""

    class Meta:
        model = EventRegistration
        fields = (
            "pk",
            "member",
            "name",
            "registered_on",
            "is_cancelled",
            "is_late_cancellation",
            "queue_position",
            "payment",
            "present",
            "avatar",
        )

    registered_on = serializers.DateTimeField(source="date")
    is_cancelled = serializers.SerializerMethodField("_is_cancelled")
    is_late_cancellation = serializers.SerializerMethodField("_is_late_cancellation")
    queue_position = serializers.SerializerMethodField("_queue_position")
    payment = PaymentTypeField(source="payment.type", choices=Payment.PAYMENT_TYPE)

    def _is_late_cancellation(self, instance):
        return instance.is_late_cancellation()

    def _queue_position(self, instance):
        pos = instance.queue_position
        return pos if pos and pos > 0 else None

    def _is_cancelled(self, instance):
        return instance.date_cancelled is not None

    def _name(self, instance):
        if instance.member:
            return instance.member.get_full_name()
        return instance.name


class EventRegistrationSerializer(serializers.ModelSerializer):
    """Registration serializer."""

    information_fields = None

    class Meta:
        model = EventRegistration
        fields = (
            "pk",
            "member",
            "name",
            "photo",
            "avatar",
            "registered_on",
            "is_late_cancellation",
            "is_cancelled",
            "queue_position",
            "fields",
            "payment",
            "present",
        )

    name = serializers.SerializerMethodField("_name")
    photo = serializers.SerializerMethodField("_photo")
    avatar = serializers.SerializerMethodField("_avatar")
    member = serializers.SerializerMethodField("_member")
    payment = PaymentTypeField(source="payment.type", choices=Payment.PAYMENT_TYPE)
    registered_on = serializers.DateTimeField(source="date", read_only=True)
    is_cancelled = serializers.SerializerMethodField("_is_cancelled")
    is_late_cancellation = serializers.SerializerMethodField("_is_late_cancellation")
    fields = serializers.HiddenField(default="")

    def _is_late_cancellation(self, instance):
        val = instance.is_late_cancellation()
        return False if val is None else val

    def _is_cancelled(self, instance):
        return instance.date_cancelled is not None

    def _member(self, instance):
        if instance.member:
            return instance.member.pk
        return None

    def _name(self, instance):
        if instance.member:
            return instance.member.profile.display_name()
        return instance.name

    def _photo(self, instance):
        if instance.member and instance.member.profile.photo:
            return self.context["request"].build_absolute_uri(
                f"{settings.MEDIA_URL}{instance.member.profile.photo}"
            )
        return self.context["request"].build_absolute_uri(
            static("members/images/default-avatar.jpg")
        )

    def _avatar(self, instance):
        placeholder = self.context["request"].build_absolute_uri(
            static("members/images/default-avatar.jpg")
        )
        file = None
        if instance.member and instance.member.profile.photo:
            file = instance.member.profile.photo
        return create_image_thumbnail_dict(
            self.context["request"], file, placeholder=placeholder, size_large="800x800"
        )

    def __init__(self, instance=None, data=empty, **kwargs):
        super().__init__(instance, data, **kwargs)
        try:
            if instance:
                self.information_fields = services.registration_fields(
                    kwargs["context"]["request"], registration=instance
                )
        except RegistrationError:
            pass

    def get_fields(self):
        fields = super().get_fields()

        if self.information_fields:
            for key, field in self.information_fields.items():
                key = "fields[{}]".format(key)
                field_type = field["type"]

                if field_type == RegistrationInformationField.BOOLEAN_FIELD:
                    fields[key] = serializers.BooleanField(
                        required=False, write_only=True
                    )
                elif field_type == RegistrationInformationField.INTEGER_FIELD:
                    fields[key] = serializers.IntegerField(
                        required=field["required"],
                        write_only=True,
                        allow_null=not field["required"],
                    )
                elif field_type == RegistrationInformationField.TEXT_FIELD:
                    fields[key] = serializers.CharField(
                        required=field["required"],
                        write_only=True,
                        allow_blank=not field["required"],
                        allow_null=not field["required"],
                    )

                fields[key].label = field["label"]
                fields[key].help_text = field["description"]
                fields[key].initial = field["value"]
                fields[key].default = field["value"]

                try:
                    if key in self.information_fields:
                        fields[key].initial = self.validated_data[key]
                except AssertionError:
                    pass

        return fields

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["fields"] = self.information_fields
        return data

    def field_values(self):
        return (
            (name[7 : len(name) - 1], value)
            for name, value in self.validated_data.items()
            if "info_field" in name
        )
