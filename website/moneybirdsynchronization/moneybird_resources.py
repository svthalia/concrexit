from moneybird.resources import ContactResourceType
from moneybirdsynchronization.models import Contact

class ContactResourceType(ContactResourceType):
    model = Contact

    @classmethod
    def get_model_kwargs(cls, resource_data):
        # This method is called when a new instance of the model is created from the data received from Moneybird.
        kwargs = super().get_model_kwargs(resource_data)
        kwargs["first_name"] = resource_data["firstname"]
        kwargs["last_name"] = resource_data["lastname"]
        kwargs["address_1"] = resource_data["address1"]
        kwargs["address_2"] = resource_data["address2"]
        kwargs["zipcode"] = resource_data["zipcode"]
        kwargs["city"] = resource_data["city"]
        kwargs["country"] = resource_data["country"]
        kwargs["email"] = resource_data["email"]
        ...
        return kwargs
        
    @classmethod
    def serialize_for_moneybird(cls, instance):
        # This method is called when the model instance is serialized for Moneybird.
        data = super().serialize_for_moneybird(instance)
        data["firstname"] = instance.first_name or ""
        data["lastname"] = instance.last_name or ""
        data["address1"] = instance.address_1 or ""
        data["address2"] = instance.address_2 or ""
        data["zipcode"] = instance.zipcode or ""
        data["city"] = instance.city or ""
        data["country"] = instance.country or ""
        data["email"] = instance.email or ""
        ...
        return data
    