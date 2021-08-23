import React, { FunctionComponent, useState, useEffect } from "react";
import { Photo } from "../../types/Photo";
import PhotoComponent from "../Photo/Photo";
import LoadingSpinner from "../LoadingSpinner/LoadingSpinner";

import { usePhotoService } from "../../services/photo-service";

const PhotoListComponent: FunctionComponent = () => {
  const [count, setCount] = useState<number>(0);
  const [photos, setPhotos] = useState<Photo[]>([]);
  const [offset, setOffset] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const photoService = usePhotoService();

  const getPhotos = async (limit: number) => {
    setError(null);
    setLoading(true);

    try {
      setPhotos([]);
      const photoList = await photoService.getPhotoList(offset, limit);
      setPhotos(photoList.results);
      setCount(photoList.count);
      setOffset(offset + limit);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  let errorText;
  if (error) {
    errorText = (
      <div>
        <p className="mt-2 text-sm text-red-600" id="error">
          {error}
        </p>
      </div>
    );
  }
  let loadingSpinner;
  if (loading) {
    loadingSpinner = (
      <div style={{ marginTop: "20px", marginLeft: "160px" }}>
        <LoadingSpinner />
      </div>
    );
  }
  return (
    <div>
      {errorText}
      <button onClick={(e) => getPhotos(56)}>Search</button>
      <br />
      {photos.map((photo) => (
        <PhotoComponent
          photo={photo}
          width={null}
          height={192}
        ></PhotoComponent>
      ))}

      {loadingSpinner}
    </div>
  );
};

export default PhotoListComponent;
