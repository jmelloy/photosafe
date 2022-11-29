from django.urls import path

from photosafe.photos.views import PhotoDayView, PhotoListView, PhotoDetailView

app_name = "photos"
urlpatterns = [
    path("blocks", view=PhotoDayView.as_view(), name="blocks"),
    path("<str:pk>/?$", view=PhotoDetailView.as_view(), name="detail"),
    path("", view=PhotoListView.as_view(), name="list"),
]
