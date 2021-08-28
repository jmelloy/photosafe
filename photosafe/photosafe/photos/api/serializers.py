from rest_framework import serializers

from photosafe.photos.models import Album, Photo


class PhotoSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.username")

    class Meta:
        model = Photo
        fields = "__all__"


class SmallPhotoSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.username")

    class Meta:
        model = Photo
        fields = [
            "uuid",
            "masterFingerprint",
            "filename",
            "original_filename",
            "date",
            "description",
            "title",
            "keywords",
            "labels",
            "height",
            "width",
            "orientation",
            "original_height",
            "original_width",
            "original_orientation",
            "original_filesize",
            "comments",
            "likes",
            "search_info",
            "s3_key_path",
            "s3_thumbnail_path",
            "s3_edited_path",
            "owner",
        ]


class AlbumSerializer(serializers.ModelSerializer):
    class Meta:
        model = Album
        fields = "__all__"
