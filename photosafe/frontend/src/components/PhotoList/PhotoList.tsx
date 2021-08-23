import React, { FunctionComponent, useState, useEffect } from "react";
import { Photo } from "../../types/Photo";
import PhotoThumbnailComponent from "../PhotoThumbnail/PhotoThumbnail";
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

  let dates = photos
    .filter(
      (value, index, array) =>
        index === 0 ||
        new Date(value.date).toDateString() !==
          new Date(array[index - 1].date).toDateString()
    )
    .map((photo) => new Date(photo.date).toDateString());
  console.log(dates);
  return (
    <div>
      {errorText}

      <button onClick={(e) => getPhotos(56)}>Search</button>
      <br />
      <br />
      {dates.map((date: string) => {
        let firstPhoto = photos.find(
          (x) => new Date(x.date).toDateString() === date
        );
        let place = [
          firstPhoto?.search_info?.city,
          firstPhoto?.search_info?.state,
          firstPhoto?.search_info?.country,
        ]
          .filter(Boolean)
          .join(", ");
        return (
          <div className="clear-left">
            <h3>
              {date} - {place}
            </h3>
            <div className="row-span-full">
              {photos
                .filter((x) => new Date(x.date).toDateString() === date)
                .map((photo) => (
                  <PhotoThumbnailComponent
                    key={photo.uuid}
                    photo={photo}
                    width={null}
                    height={192}
                  ></PhotoThumbnailComponent>
                ))}
            </div>
            <br />
          </div>
        );
      })}

      {loadingSpinner}
    </div>
  );
};

export default PhotoListComponent;
