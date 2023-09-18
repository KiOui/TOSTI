from django.urls import path
from age.api.v1.views import YiviStartAPIView, YiviResultAPIView


urlpatterns = [
    path("start/", YiviStartAPIView.as_view(), name="yivi_start"),
    path("result/", YiviResultAPIView.as_view(), name="yivi_result"),
]
