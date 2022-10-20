class CurrentRequestObjectDefault:
    """A default class that can be used to represent an object based on the request arguments.

    In order to use this, the 'request' must have been provided as part
    of the context dictionary when instantiating the serializer.
    """

    requires_context = True

    def __init__(self, model, url_field, model_field="pk") -> None:
        super().__init__()
        self.model = model
        self.model_field = model_field
        self.url_field = url_field

    def __call__(self, serializer_field):
        val = serializer_field.context["view"].kwargs.get(
            serializer_field.context["view"].lookup_field, None
        )
        if self.url_field:
            val = serializer_field.context["view"].kwargs.get(self.url_field, None)
        return self.model.objects.get(**{self.model_field: val})

    def __repr__(self):
        return f"{self.__class__.__name__}()"
