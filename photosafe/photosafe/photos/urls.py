from django.urls import path

from photosafe.photos.views import PhotoDayView

app_name = "photos"
urlpatterns = [
    path("blocks", view=PhotoDayView.as_view(), name="blocks"),
]
