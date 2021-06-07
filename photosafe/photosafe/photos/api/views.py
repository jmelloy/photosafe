from rest_framework.mixins import *
from rest_framework.viewsets import GenericViewSet
from django_filters import rest_framework as filters

from .serializers import PhotoSerializer, AlbumSerializer
from photosafe.photos.models import *

class PhotoFilter(filters.FilterSet):
    albums = filters.CharFilter(lookup_expr='contains')
    date = filters.IsoDateTimeFilter()

    class Meta:
        model = Photo
        fields = ["original_filename", "albums", "date"]


class PhotoViewSet(RetrieveModelMixin, ListModelMixin, CreateModelMixin, UpdateModelMixin, GenericViewSet):
    serializer_class = PhotoSerializer
    queryset = Photo.objects.all()
    lookup_field = "uuid"

    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = PhotoFilter

class AlbumViewSet(RetrieveModelMixin, ListModelMixin, CreateModelMixin, UpdateModelMixin, GenericViewSet):
    serializer_class = AlbumSerializer
    queryset = Album.objects.all()
    lookup_field = "uuid"
    filter_backends = (filters.DjangoFilterBackend,)
