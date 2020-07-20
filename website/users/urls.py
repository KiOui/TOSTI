from django.urls import path
from .views import LoginView, VerifyView, LogoutView, AccountView

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("verify/", VerifyView.as_view(), name="verify"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("account/", AccountView.as_view(), name="account"),
]
