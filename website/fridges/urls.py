from django.urls import path

from fridges import views

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
]
