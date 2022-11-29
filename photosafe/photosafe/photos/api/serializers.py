from rest_framework import serializers

from photosafe.photos.models import Album, Photo, Version


class VersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Version
        fields = ["version", "s3_path", "filename", "width", "height", "size"]


class PhotoSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.username")

    versions = VersionSerializer(many=True, required=False)

    class Meta:
        model = Photo
        fields = "__all__"

    # https://www.django-rest-framework.org/api-guide/relations/
    def create(self, validated_data):
        versions = validated_data.pop("versions")
        photo = Photo.objects.create(**validated_data)

        for version in versions:
            Version.objects.create(photo=photo, **version)
        return photo

    def update(self, instance, validated_data):
        print(validated_data)

        versions = validated_data.pop("versions")

        instance = super(PhotoSerializer, self).update(instance, validated_data)

        for version in versions:
            Version.objects.update_or_create(
                photo=instance, version=version["version"], defaults=version
            )

        return instance


class SmallPhotoSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.username")

    class Meta:
        model = Photo
        fields = [
            "uuid",
            "masterFingerprint",
            # "filename",
            "original_filename",
            "date",
            "description",
            "title",
            "keywords",
            "labels",
            "height",
            "width",
            "orientation",
            "height",
            "width",
            "orientation",
            "size",
            "search_info",
            "s3_key_path",
            "s3_thumbnail_path",
            "owner",
        ]


class AlbumSerializer(serializers.ModelSerializer):
    class Meta:
        model = Album
        fields = "__all__"
