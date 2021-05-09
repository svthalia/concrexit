from rest_framework.fields import HiddenField


class CurrentMemberField(HiddenField):
    """The current member field does not take input from the user, or present any output,
    but it does populate a field in `validated_data`, based on the member in the current request."""

    def __init__(self, **kwargs):
        kwargs["default"] = None
        super().__init__(**kwargs)

    def get_value(self, dictionary):
        return self.context["request"].member
