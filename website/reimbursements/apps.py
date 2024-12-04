from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ReimbursementsConfig(AppConfig):
    """AppConfig for the announcement package."""

    name = "reimbursements"
    verbose_name = _("Site reimbursements")
