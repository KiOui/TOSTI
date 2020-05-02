from django.urls import path
from .views import LoginView, VerifyView, LogoutView

urlpatterns = [
    path("login", LoginView.as_view(), name="login"),
    path("verify", VerifyView.as_view(), name="verify"),
    path("logout", LogoutView.as_view(), name="logout"),
]
