from django_filters import rest_framework as filters
from rest_framework.mixins import (
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.viewsets import GenericViewSet

from photosafe.photos.models import *

from .serializers import AlbumSerializer, PhotoSerializer


class PhotoFilter(filters.FilterSet):
    albums = filters.CharFilter(lookup_expr="contains")
    date = filters.IsoDateTimeFilter()

    class Meta:
        model = Photo
        fields = ["original_filename", "albums", "date"]


class PhotoViewSet(
    RetrieveModelMixin,
    ListModelMixin,
    CreateModelMixin,
    UpdateModelMixin,
    GenericViewSet,
):
    serializer_class = PhotoSerializer
    queryset = Photo.objects.all()
    lookup_field = "uuid"

    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = PhotoFilter

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class AlbumViewSet(
    RetrieveModelMixin,
    ListModelMixin,
    CreateModelMixin,
    UpdateModelMixin,
    GenericViewSet,
):
    serializer_class = AlbumSerializer
    queryset = Album.objects.all()
    lookup_field = "uuid"
    filter_backends = (filters.DjangoFilterBackend,)
