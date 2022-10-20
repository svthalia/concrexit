from django.contrib.admin.models import ADDITION, CHANGE, DELETION, LogEntry
from django.contrib.admin.options import get_content_type_for_model

from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)
from rest_framework.permissions import IsAdminUser

from thaliawebsite.api.v2.admin.model.diff import ModelDiffCalculator
from thaliawebsite.api.v2.admin.permissions import DjangoAdminModelPermissions


class AdminPermissionsMixin:
    def get_permissions(self):
        self.permission_classes.append(IsAdminUser)
        self.permission_classes.append(DjangoAdminModelPermissions)
        return super().get_permissions()


class LogActionMixin:
    def log_action(self, request, object, flag=ADDITION, message=None):
        """Log that an object has been successfully added.

        The default implementation creates an admin LogEntry object.
        """
        return LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=get_content_type_for_model(object).pk,
            object_id=object.pk,
            object_repr=str(object),
            action_flag=flag,
            change_message=message,
        )


class AdminListAPIView(AdminPermissionsMixin, ListAPIView):
    pass


class AdminRetrieveAPIView(AdminPermissionsMixin, RetrieveAPIView):
    pass


class AdminCreateAPIView(AdminPermissionsMixin, LogActionMixin, CreateAPIView):
    def perform_create(self, serializer):
        super().perform_create(serializer)
        self.log_action(
            self.request,
            serializer.instance,
            ADDITION,
            [
                {
                    "added": {
                        "name": str(serializer.instance._meta.verbose_name),
                        "object": str(serializer.instance),
                    }
                }
            ],
        )


class AdminUpdateAPIView(AdminPermissionsMixin, LogActionMixin, UpdateAPIView):
    def perform_update(self, serializer):
        helper = ModelDiffCalculator(self.get_object())
        super().perform_update(serializer)
        self.log_action(
            self.request,
            serializer.instance,
            CHANGE,
            [
                {
                    "changed": {
                        "name": str(serializer.instance._meta.verbose_name),
                        "object": str(serializer.instance),
                        "fields": helper.set_changed_model(
                            serializer.instance
                        ).changed_fields,
                    }
                }
            ],
        )


class AdminDestroyAPIView(AdminPermissionsMixin, LogActionMixin, DestroyAPIView):
    def perform_destroy(self, instance):
        log_message = [
            {
                "deleted": {
                    "name": str(instance._meta.verbose_name),
                    "object": str(instance),
                }
            }
        ]
        super().perform_destroy(instance)
        self.log_action(self.request, instance, DELETION, log_message)
