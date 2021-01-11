from django.urls import path, include

app_name = "tosti"

urlpatterns = [
    path("", include("orders.api.v1.urls")),
]
