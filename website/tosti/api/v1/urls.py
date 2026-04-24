from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView

app_name = "tosti"

urlpatterns = [
    path("", include("orders.api.v1.urls")),
    path("thaliedje/", include("thaliedje.api.v1.urls")),
    path("venues/", include("venues.api.v1.urls")),
    path("associations/", include("associations.api.v1.urls")),
    path("transactions/", include("transactions.api.v1.urls")),
    path("users/", include("users.api.v1.urls")),
    path("yivi/", include("yivi.api.v1.urls")),
    path("fridges/", include("fridges.api.v1.urls")),
    path("schema", SpectacularAPIView.as_view(api_version="v1"), name="schema-v1"),
]
