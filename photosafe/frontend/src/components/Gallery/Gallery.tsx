import React, { useState, useEffect } from "react";
import { Photo } from "../../types/Photo";
import PhotoComponent from "../Photo/Photo";

import { useGallery } from "../../services/photo-service";

export default function GalleryComponent() {
  const [count, setCount] = useState<number>(0);
  const [photos, setPhotos] = useState<Photo[]>([]);
  const [error, setError] = useState<string | null>(null);

  const gallery = useGallery();

  useEffect(() => {
    const loadGallery = async () => {
      try {
        const photoList = await gallery.getPhotoList();
        setCount(photoList?.count || 0);
        setPhotos(photoList?.results || []);
      } catch (err) {
        setError(err.message);
      }
    };
    loadGallery();
  }, [gallery]);

  if (error) {
    return (
      <div>
        <p className="mt-2 text-sm text-red-600" id="error">
          {error}
        </p>
      </div>
    );
  }

  return (
    <div>
      {photos.map((photo) => (
        <PhotoComponent photo={photo}></PhotoComponent>
      ))}
    </div>
  );
}
