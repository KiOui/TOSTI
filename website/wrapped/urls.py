from django.urls import path

from wrapped import views

urlpatterns = [
    path("<int:year>/", views.StoryView.as_view(), name="story"),
]
