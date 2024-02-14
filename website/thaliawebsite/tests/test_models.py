from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.test import TestCase

# Third-party apps whose models haven't implemented __str__ overrides.
_EXCLUDED_APPS = {
    "django_drf_filepond",
    "thumbnails",
    "otp_static",
    "otp_totp",
}


def create_models_test_class(classname):
    """Create the class for all the model __str__ tests.

    This class is created dynamically with the type(name, bases, dict)
    function, it includes test functions to test all the models in the project.

    :param classname: The name to use for the created class
    :return: An instance of the TestCase class with generated tests
    """

    def create_model_test_function(name, test_model):
        """Create a test function that tests database model test_model."""

        def str_function_is_overwritten_for(self):
            """Check if the test_model overrides __str__.

            Compares the implementation to the super class version.
            """
            instance = test_model()
            try:
                # the implemented __str__ method should be different from the
                # __str__ function in the parent class (Model)
                self.assertNotEqual(str(instance), models.Model.__str__(instance))
            except (ObjectDoesNotExist, AttributeError, KeyError, TypeError):
                # if the __str__ method relies on any fields which were not
                # instantiated, it throws a derivative of ObjectDoesNotExist,
                # or one of the other errors which means it is different from
                # the parent class implementation
                pass

        # the testing framework uses qualname to print the method name and
        # its class
        str_function_is_overwritten_for.__qualname__ = f"{classname}.{name}"
        str_function_is_overwritten_for.__name__ = name
        return str_function_is_overwritten_for

    tests = {}
    # django keeps track of the models it knows of, and we can request that
    # here by default these are only the models implemented by the project
    for model in apps.get_models():
        if model._meta.app_label in _EXCLUDED_APPS:
            continue
        funcname = f"test_str_method_overwritten_for_{model.__name__}"
        tests[funcname] = create_model_test_function(funcname, model)

    # type() is the class constructor, it's arguments are
    # name: name of the class
    # bases: classes the new class inherits from
    # dict: attributes (which includes methods) of this class
    return type(classname, (TestCase,), tests)


# create the class to be picked up by the django test runner
ModelsTest = create_models_test_class("ModelsTest")
