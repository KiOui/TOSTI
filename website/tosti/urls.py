"""
TOSTI URL Configuration.

The `urlpatterns` list routes URLs to views. For more information please see:
https://docs.djangoproject.com/en/2.2/topics/http/urls/

Examples:
Function views

1. Add an import:  from my_app import views
2. Add a URL to urlpatterns:  path('', views.home, name='home')

Class-based views

1. Add an import:  from other_app.views import Home
2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')

Including another URLconf

1. Import the include() function: from django.urls import include, path
2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from .views import (
    IndexView,
    PrivacyView,
    handler403 as custom_handler403,
    handler404 as custom_handler404,
    handler500 as custom_handler500,
)

handler403 = custom_handler403
handler404 = custom_handler404
handler500 = custom_handler500

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", IndexView.as_view(), name="index"),
    path("privacy/", PrivacyView.as_view(), name="privacy"),
    path("users/", include(("users.urls", "users"), namespace="users"),),
    path("shifts/", include(("orders.urls", "orders"), namespace="orders"),),
    path("marietje/", include(("marietje.urls", "marietje"), namespace="marietje"),),
    path("api/", include([path("v1/", include("tosti.api.v1.urls"))])),
]
