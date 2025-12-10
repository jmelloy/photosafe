from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from photosafe.users.api.views import UserViewSet
from photosafe.photos.api.views import PhotoViewSet, AlbumViewSet

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register("users", UserViewSet)
router.register("photos", PhotoViewSet)
router.register("albums", AlbumViewSet)

app_name = "api"
urlpatterns = router.urls
