from django.db import models


class FunctionalPermissions(models.Model):
    """Custom auxiliary model to define functional non-model permissions."""

    class Meta:
        managed = False  # Don't create a table for this model
        default_permissions = ()  # disable "add", "change", "delete" and "view" default permissions
        permissions = (("email_sender", "Send emails using the email sender"),)

    def __str__(self):
        return "Functional permissions"
