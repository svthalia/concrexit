from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags
from html import unescape
from rest_framework import serializers
from rest_framework.fields import empty

from thaliawebsite.api.services import create_image_thumbnail_dict
from events import services
from events.exceptions import RegistrationError
from events.models import Event, Registration, RegistrationInformationField
from pizzas.models import PizzaEvent
from thaliawebsite.settings import settings


class CalenderJSSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            'start', 'end', 'all_day', 'is_birthday',
            'url', 'title', 'description',
            'backgroundColor', 'textColor', 'blank',
            'registered'
        )

    start = serializers.SerializerMethodField('_start')
    end = serializers.SerializerMethodField('_end')
    all_day = serializers.SerializerMethodField('_all_day')
    is_birthday = serializers.SerializerMethodField('_is_birthday')
    url = serializers.SerializerMethodField('_url')
    title = serializers.SerializerMethodField('_title')
    description = serializers.SerializerMethodField('_description')
    backgroundColor = serializers.SerializerMethodField('_background_color')
    textColor = serializers.SerializerMethodField('_text_color')
    blank = serializers.SerializerMethodField('_target_blank')
    registered = serializers.SerializerMethodField('_registered')

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

    def _registered(self, instance):
        return None


class EventCalenderJSSerializer(CalenderJSSerializer):
    class Meta(CalenderJSSerializer.Meta):
        model = Event

    def _url(self, instance):
        return reverse('events:event', kwargs={'pk': instance.id})

    def _registered(self, instance):
        try:
            return services.is_user_registered(instance,
                                               self.context['member'])
        except AttributeError:
            return None


class UnpublishedEventSerializer(CalenderJSSerializer):
    class Meta(CalenderJSSerializer.Meta):
        model = Event

    def _background_color(self, instance):
        return "#888888"

    def _text_color(self, instance):
        return "white"

    def _url(self, instance):
        return reverse('events:admin-details', kwargs={
            'event_id': instance.id})


class EventRetrieveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ('pk', 'title', 'description', 'start', 'end', 'organiser',
                  'category', 'registration_start', 'registration_end',
                  'cancel_deadline', 'location', 'map_location', 'price',
                  'fine', 'max_participants', 'num_participants', 'status',
                  'user_registration', 'registration_allowed',
                  'no_registration_message', 'has_fields')

    description = serializers.SerializerMethodField('_description')
    user_registration = serializers.SerializerMethodField('_user_registration')
    num_participants = serializers.SerializerMethodField('_num_participants')
    registration_allowed = serializers.SerializerMethodField(
        '_registration_allowed')
    has_fields = serializers.SerializerMethodField('_has_fields')
    status = serializers.SerializerMethodField('_status')  # DEPRECATED

    REGISTRATION_NOT_NEEDED = -1
    REGISTRATION_NOT_YET_OPEN = 0
    REGISTRATION_OPEN = 1
    REGISTRATION_OPEN_NO_CANCEL = 2
    REGISTRATION_CLOSED = 3
    REGISTRATION_CLOSED_CANCEL_ONLY = 4

    """ DEPRECATED """

    def _status(self, instance):
        now = timezone.now()
        if instance.registration_start or instance.registration_end:
            if now <= instance.registration_start:
                return self.REGISTRATION_NOT_YET_OPEN
            elif (instance.registration_end <= now
                    < instance.cancel_deadline):
                return self.REGISTRATION_CLOSED_CANCEL_ONLY
            elif (instance.cancel_deadline <= now <
                    instance.registration_end):
                return self.REGISTRATION_OPEN_NO_CANCEL
            elif (now >= instance.registration_end and
                    now >= instance.cancel_deadline):
                return self.REGISTRATION_CLOSED
            else:
                return self.REGISTRATION_OPEN
        else:
            return self.REGISTRATION_NOT_NEEDED

    def _description(self, instance):
        return unescape(strip_tags(instance.description))

    def _num_participants(self, instance):
        if (instance.max_participants and
                instance.participants.count() > instance.max_participants):
            return instance.max_participants
        return instance.participants.count()

    def _user_registration(self, instance):
        try:
            reg = instance.registration_set.get(
                member=self.context['request'].member)
            return RegistrationListSerializer(reg, context=self.context).data
        except Registration.DoesNotExist:
            return None

    def _registration_allowed(self, instance):
        member = self.context['request'].member
        return (member.has_active_membership and
                member.can_attend_events)

    def _has_fields(self, instance):
        return instance.has_fields()


class EventListSerializer(serializers.ModelSerializer):
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
            return services.is_user_registered(
                instance, self.context['request'].user)
        except AttributeError:
            return None

    def _pizza(self, instance):
        pizza_events = PizzaEvent.objects.filter(event=instance)
        return pizza_events.exists()


class RegistrationListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Registration
        fields = ('pk', 'member', 'name', 'photo', 'avatar', 'registered_on',
                  'is_late_cancellation', 'is_cancelled', 'queue_position')

    name = serializers.SerializerMethodField('_name')
    photo = serializers.SerializerMethodField('_photo')
    avatar = serializers.SerializerMethodField('_avatar')
    member = serializers.SerializerMethodField('_member')
    registered_on = serializers.DateTimeField(source='date')
    is_cancelled = serializers.SerializerMethodField('_is_cancelled')
    is_late_cancellation = serializers.SerializerMethodField(
        '_is_late_cancellation')
    queue_position = serializers.SerializerMethodField(
        '_queue_position', read_only=False)

    def _is_late_cancellation(self, instance):
        return instance.is_late_cancellation()

    def _queue_position(self, instance):
        pos = instance.queue_position
        return pos if pos > 0 else None

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


class RegistrationSerializer(serializers.ModelSerializer):
    information_fields = None

    class Meta:
        model = Registration
        fields = ('pk', 'member', 'name', 'photo', 'avatar', 'registered_on',
                  'is_late_cancellation', 'is_cancelled',
                  'queue_position', 'fields')

    name = serializers.SerializerMethodField('_name')
    photo = serializers.SerializerMethodField('_photo')
    avatar = serializers.SerializerMethodField('_avatar')
    member = serializers.SerializerMethodField('_member')
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
                    instance.member, instance.event)
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
