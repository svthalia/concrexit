from thaliawebsite.api.v2.admin import DjangoAdminModelPermissions


class DjangoAdminModelViewPermissions(DjangoAdminModelPermissions):
    perms_map = {
        "GET": ["%(app_label)s.view_%(model_name)s"],
        "OPTIONS": ["%(app_label)s.view_%(model_name)s"],
        "HEAD": ["%(app_label)s.view_%(model_name)s"],
        "POST": [],
        "PUT": [],
        "PATCH": [],
        "DELETE": [],
    }
