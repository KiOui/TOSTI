from django.urls import path
from age.api.v1.views import YiviStartAPIView, YiviResultAPIView


urlpatterns = [
    path("session/", YiviStartAPIView.as_view(), name="yivi_start"),
    path("session/<str:pk>/result/", YiviResultAPIView.as_view(), name="yivi_result"),
]
