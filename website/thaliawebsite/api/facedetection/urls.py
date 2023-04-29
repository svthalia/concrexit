from django.urls import include, path

app_name = "thaliawebsite"

urlpatterns = [
    path("", include("facedetection.api.facedetection.urls")),
]
