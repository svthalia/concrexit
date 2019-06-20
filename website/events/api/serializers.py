from django.conf import settings
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags, strip_spaces_between_tags
from html import unescape
from rest_framework import serializers
from rest_framework.fields import empty

from payments.api.fields import PaymentTypeField
from payments.models import Payment
from thaliawebsite.api.services import create_image_thumbnail_dict
from events import services
from events.exceptions import RegistrationError
from events.models import Event, Registration, RegistrationInformationField
from pizzas.models import PizzaEvent
from thaliawebsite.templatetags.bleach_tags import bleach
from utils.snippets import create_google_maps_url


class CalenderJSSerializer(serializers.ModelSerializer):
    """
    Serializer using the right format for CalendarJS
    """
    class Meta:
        fields = (
            'start', 'end', 'allDay', 'isBirthday',
            'url', 'title', 'description',
            'backgroundColor', 'textColor', 'blank'
        )

    start = serializers.SerializerMethodField('_start')
    end = serializers.SerializerMethodField('_end')
    allDay = serializers.SerializerMethodField('_all_day')
    isBirthday = serializers.SerializerMethodField('_is_birthday')
    url = serializers.SerializerMethodField('_url')
    title = serializers.SerializerMethodField('_title')
    description = serializers.SerializerMethodField('_description')
    backgroundColor = serializers.SerializerMethodField('_background_color')
    textColor = serializers.SerializerMethodField('_text_color')
    blank = serializers.SerializerMethodField('_target_blank')

    def _start(self, instance):
        return timezone.localtime(instance.start)

    def _end(self, instance):
        return timezone.localtime(instance.end)

    def _all_day(self, instance):
        return False

    def _is_birthday(self, instance):
        return False

    def _url(self, instance):
        raise NotImplementedError

    def _title(self, instance):
        return instance.title

    def _description(self, instance):
        return unescape(strip_tags(instance.description))

    def _background_color(self, instance):
        pass

    def _text_color(self, instance):
        pass

    def _target_blank(self, instance):
        return False


class EventCalenderJSSerializer(CalenderJSSerializer):
    class Meta(CalenderJSSerializer.Meta):
        model = Event

    def _url(self, instance):
        return reverse('events:event', kwargs={'pk': instance.id})

    def _background_color(self, instance):
        try:
            if services.is_user_registered(self.context['member'],
                                           instance):
                return "#E62272"
        except AttributeError:
            pass
        return "#616161"

    def _text_color(self, instance):
        return "#FFFFFF"


class UnpublishedEventSerializer(CalenderJSSerializer):
    """
    See CalenderJSSerializer, customised colors
    """
    class Meta(CalenderJSSerializer.Meta):
        model = Event

    def _background_color(self, instance):
        return "rgba(255,0,0,0.3)"

    def _text_color(self, instance):
        return "black"

    def _url(self, instance):
        return reverse('admin:events_event_details', kwargs={
            'pk': instance.id})


class EventRetrieveSerializer(serializers.ModelSerializer):
    """
    Serializer for events
    """
    class Meta:
        model = Event
        fields = ('pk', 'title', 'description', 'start', 'end', 'organiser',
                  'category', 'registration_start', 'registration_end',
                  'cancel_deadline', 'location', 'map_location', 'price',
                  'fine', 'max_participants', 'num_participants',
                  'user_registration', 'registration_allowed',
                  'no_registration_message', 'has_fields', 'is_pizza_event',
                  'google_maps_url', 'is_admin')

    description = serializers.SerializerMethodField('_description')
    user_registration = serializers.SerializerMethodField('_user_registration')
    num_participants = serializers.SerializerMethodField('_num_participants')
    registration_allowed = serializers.SerializerMethodField(
        '_registration_allowed')
    has_fields = serializers.SerializerMethodField('_has_fields')
    is_pizza_event = serializers.SerializerMethodField('_is_pizza_event')
    google_maps_url = serializers.SerializerMethodField('_google_maps_url')
    is_admin = serializers.SerializerMethodField('_is_admin')

    def _description(self, instance):
        return strip_spaces_between_tags(bleach(instance.description))

    def _num_participants(self, instance):
        if (instance.max_participants and
                instance.participants.count() > instance.max_participants):
            return instance.max_participants
        return instance.participants.count()

    def _user_registration(self, instance):
        try:
            if self.context['request'].member:
                reg = instance.registration_set.get(
                    member=self.context['request'].member)
                return RegistrationAdminListSerializer(
                    reg, context=self.context).data
        except Registration.DoesNotExist:
            pass
        return None

    def _registration_allowed(self, instance):
        member = self.context['request'].member
        return (self.context['request'].user.is_authenticated and
                member.has_active_membership and
                member.can_attend_events)

    def _has_fields(self, instance):
        return instance.has_fields()

    def _is_pizza_event(self, instance):
        return instance.is_pizza_event()

    def _google_maps_url(self, instance):
        return create_google_maps_url(
                instance.map_location,
                zoom=13,
                size='450x250')

    def _is_admin(self, instance):
        member = self.context['request'].member
        return services.is_organiser(member, instance)


class EventListSerializer(serializers.ModelSerializer):
    """Custom list serializer for events"""
    class Meta:
        model = Event
        fields = ('pk', 'title', 'description', 'start', 'end',
                  'location', 'price', 'registered', 'pizza')

    description = serializers.SerializerMethodField('_description')
    registered = serializers.SerializerMethodField('_registered')
    pizza = serializers.SerializerMethodField('_pizza')

    def _description(self, instance):
        return unescape(strip_tags(instance.description))

    def _registered(self, instance):
        try:
            return services.is_user_registered(self.context['request'].user,
                                               instance)
        except AttributeError:
            return None

    def _pizza(self, instance):
        pizza_events = PizzaEvent.objects.filter(event=instance)
        return pizza_events.exists()


class RegistrationListSerializer(serializers.ModelSerializer):
    """Custom registration list serializer"""
    class Meta:
        model = Registration
        fields = ('pk', 'member', 'name', 'avatar')

    name = serializers.SerializerMethodField('_name')
    avatar = serializers.SerializerMethodField('_avatar')
    member = serializers.SerializerMethodField('_member')

    def _member(self, instance):
        if instance.member:
            return instance.member.pk
        return None

    def _name(self, instance):
        if instance.member:
            return instance.member.profile.display_name()
        return instance.name

    def _avatar(self, instance):
        placeholder = self.context['request'].build_absolute_uri(
            static('members/images/default-avatar.jpg'))
        file = None
        if instance.member and instance.member.profile.photo:
            file = instance.member.profile.photo
        return create_image_thumbnail_dict(
            self.context['request'], file, placeholder=placeholder,
            size_large='800x800')


class RegistrationAdminListSerializer(RegistrationListSerializer):
    """Custom registration admin list serializer"""
    class Meta:
        model = Registration
        fields = ('pk', 'member', 'name', 'registered_on', 'is_cancelled',
                  'is_late_cancellation', 'queue_position', 'payment',
                  'present', 'avatar')

    registered_on = serializers.DateTimeField(source='date')
    is_cancelled = serializers.SerializerMethodField('_is_cancelled')
    is_late_cancellation = serializers.SerializerMethodField(
        '_is_late_cancellation')
    queue_position = serializers.SerializerMethodField('_queue_position')
    payment = PaymentTypeField(source='payment.type',
                               choices=Payment.PAYMENT_TYPE)

    def _is_late_cancellation(self, instance):
        return instance.is_late_cancellation()

    def _queue_position(self, instance):
        pos = instance.queue_position
        return pos if pos > 0 else None

    def _is_cancelled(self, instance):
        return instance.date_cancelled is not None

    def _name(self, instance):
        if instance.member:
            return instance.member.get_full_name()
        return instance.name


class RegistrationSerializer(serializers.ModelSerializer):
    """Registration serializer"""
    information_fields = None

    class Meta:
        model = Registration
        fields = ('pk', 'member', 'name', 'photo', 'avatar', 'registered_on',
                  'is_late_cancellation', 'is_cancelled',
                  'queue_position', 'fields',
                  'payment', 'present')

    name = serializers.SerializerMethodField('_name')
    photo = serializers.SerializerMethodField('_photo')
    avatar = serializers.SerializerMethodField('_avatar')
    member = serializers.SerializerMethodField('_member')
    payment = PaymentTypeField(source='payment.type',
                               choices=Payment.PAYMENT_TYPE)
    registered_on = serializers.DateTimeField(source='date', read_only=True)
    is_cancelled = serializers.SerializerMethodField('_is_cancelled')
    is_late_cancellation = serializers.SerializerMethodField(
        '_is_late_cancellation')
    queue_position = serializers.SerializerMethodField(
        '_queue_position', read_only=False)
    fields = serializers.HiddenField(default='')

    def _is_late_cancellation(self, instance):
        val = instance.is_late_cancellation()
        return False if val is None else val

    def _is_cancelled(self, instance):
        return instance.date_cancelled is not None

    def _queue_position(self, instance):
        pos = instance.queue_position
        return pos if pos > 0 else None

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
            return self.context['request'].build_absolute_uri(
                '%s%s' % (settings.MEDIA_URL, instance.member.profile.photo))
        else:
            return self.context['request'].build_absolute_uri(
                static('members/images/default-avatar.jpg'))

    def _avatar(self, instance):
        placeholder = self.context['request'].build_absolute_uri(
            static('members/images/default-avatar.jpg'))
        file = None
        if instance.member and instance.member.profile.photo:
            file = instance.member.profile.photo
        return create_image_thumbnail_dict(
            self.context['request'], file, placeholder=placeholder,
            size_large='800x800')

    def __init__(self, instance=None, data=empty, **kwargs):
        super().__init__(instance, data, **kwargs)
        try:
            if instance:
                self.information_fields = services.registration_fields(
                    kwargs['context']['request'],
                    registration=instance)
        except RegistrationError:
            pass

    def get_fields(self):
        fields = super().get_fields()

        if self.information_fields:
            for key, field in self.information_fields.items():
                key = 'fields[{}]'.format(key)
                field_type = field['type']

                if field_type == RegistrationInformationField.BOOLEAN_FIELD:
                    fields[key] = serializers.BooleanField(
                        required=False,
                        write_only=True
                    )
                elif field_type == RegistrationInformationField.INTEGER_FIELD:
                    fields[key] = serializers.IntegerField(
                        required=field['required'],
                        write_only=True
                    )
                elif field_type == RegistrationInformationField.TEXT_FIELD:
                    fields[key] = serializers.CharField(
                        required=field['required'],
                        write_only=True
                    )

                fields[key].label = field['label']
                fields[key].help_text = field['description']
                fields[key].initial = field['value']
                fields[key].default = field['value']

                try:
                    if key in self.information_fields:
                        fields[key].initial = self.validated_data[key]
                except AssertionError:
                    pass

        return fields

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['fields'] = self.information_fields
        return data

    def field_values(self):
        return ((name[7:len(name) - 1], value)
                for name, value in self.validated_data.items()
                if "info_field" in name)
