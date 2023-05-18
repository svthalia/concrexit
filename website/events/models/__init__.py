"""The models defined by the events package."""

from .event import Event
from .event_registration import EventRegistration
from .feed_token import FeedToken
from .registration_information_field import (
    BooleanRegistrationInformation,
    IntegerRegistrationInformation,
    RegistrationInformationField,
    TextRegistrationInformation,
)

__all__ = [
    "Event",
    "EventRegistration",
    "FeedToken",
    "BooleanRegistrationInformation",
    "IntegerRegistrationInformation",
    "RegistrationInformationField",
    "TextRegistrationInformation",
]
