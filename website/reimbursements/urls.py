from django.urls import path

from reimbursements.views import CreateReimbursementView, IndexView

app_name = "reimbursements"

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("create/", CreateReimbursementView.as_view(), name="create"),
]
