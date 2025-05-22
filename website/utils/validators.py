from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _


@deconstructible
class RangeValueValidator:
    messages = {
        "upper_excl": _("Value must be smaller than %(upper)s."),
        "upper_incl": _("Value may not exceed %(upper)s."),
        "lower_excl": _("Value must be greater than %(lower)s."),
        "lower_incl": _("Value must at least %(lower)s."),
        "lower_excl_upper_excl": _(
            "Value must be between %(lower)s and %(upper)s (not inclusive)."
        ),
        "lower_incl_upper_excl": _(
            "Value must be at least %(lower)s and less than %(upper)s."
        ),
        "lower_excl_upper_incl": _(
            "Value must be greater than %(lower)s and at most %(upper)s."
        ),
        "lower_incl_upper_incl": _(
            "Value must be at least %(lower)s and at most %(upper)s."
        ),
    }

    def select_error_message(self):
        build_tuple = (
            self.lower,
            self.lower_inclusive,
            self.upper,
            self.upper_inclusive,
        )

        match build_tuple:
            case (None, _, None, _):
                return
            case (None, _, _, False):
                return self.messages["upper_excl"]
            case (None, _, _, True):
                return self.messages["upper_incl"]
            case (_, False, None, _):
                return self.messages["lower_excl"]
            case (_, True, None, _):
                return self.messages["lower_incl"]
            case (_, False, _, False):
                return self.messages["lower_excl_upper_excl"]
            case (_, False, _, True):
                return self.messages["lower_excl_upper_incl"]
            case (_, True, _, False):
                return self.messages["lower_incl_upper_excl"]
            case (_, True, _, True):
                return self.messages["lower_incl_upper_incl"]
            case _:
                return

    def __init__(
        self,
        lower=None,
        lower_inclusive: bool = False,
        upper=None,
        upper_inclusive: bool = False,
    ):
        self.lower = lower
        self.lower_inclusive = lower_inclusive
        self.upper = upper
        self.upper_inclusive = upper_inclusive

        # Set lower_inclusive and upper_inclusive to False if no lower or upper respectively
        if not self.upper:
            self.upper_inclusive = False
        if not self.lower:
            self.lower_inclusive = False

        self.error_message = self.select_error_message()

    def __call__(self, value):
        if self.lower:
            if self.lower_inclusive:
                if value < self.lower:
                    raise ValidationError(self.error_message)
            else:
                if value <= self.lower:
                    raise ValidationError(self.error_message)

        if self.upper:
            if self.upper_inclusive:
                if value > self.upper:
                    raise ValidationError(self.error_message)
            else:
                if value >= self.upper:
                    raise ValidationError(self.error_message)
