class CurrentMemberDefault:
    """A default class that can be used to represent the current member.

    In order to use this, the 'request' must have been provided as part
    of the context dictionary when instantiating the serializer.
    """

    requires_context = True

    def __call__(self, serializer_field):
        return serializer_field.context["request"].member

    def __repr__(self):
        return "%s()" % self.__class__.__name__
