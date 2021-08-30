import React, {
  FunctionComponent,
  useState,
  useEffect,
  FormEventHandler,
  FormEvent,
} from "react";
import { Photo } from "../../types/Photo";
import PhotoThumbnailComponent from "../PhotoThumbnail/PhotoThumbnail";
import LoadingSpinner from "../LoadingSpinner/LoadingSpinner";

import { usePhotoService } from "../../services/photo-service";
import { Link, useParams } from "react-router-dom";
import Pagination from "../Pagination";

type Params = {
  page: string;
};

const PhotoListComponent: FunctionComponent = () => {
  const [count, setCount] = useState<number>(0);
  const [photos, setPhotos] = useState<Photo[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const photoService = usePhotoService();

  const params: Params = useParams();
  const page = parseInt(params.page, 10) || 1;

  useEffect(() => {
    const getPhotos = async () => {
      setError(null);
      setLoading(true);
      let limit = 56;

      try {
        // setPhotos([]);
        const photoList = await photoService.getPhotoList(
          (page - 1) * limit,
          limit
        );
        setPhotos(photoList.results);
        setCount(photoList.count);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    getPhotos();
  }, [photoService, page]);

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

  return (
    <div>
      <Pagination total={count} page={page} perPage={56}></Pagination>

      {errorText}
      {loadingSpinner}
      {dates.map((date: string) => {
        let firstPhoto = photos.find(
          (x) => new Date(x.date).toDateString() === date
        );

        return (
          <div className="clear-left">
            <h3>
              {date} - {firstPhoto?.place?.name}
            </h3>
            <div className="row-span-full">
              {photos
                .filter((x) => new Date(x.date).toDateString() === date)
                .map((photo) => (
                  <Link to={`/photos/${photo.uuid}`}>
                    <PhotoThumbnailComponent
                      key={photo.uuid}
                      photo={photo}
                      width={null}
                      height={192}
                    ></PhotoThumbnailComponent>
                  </Link>
                ))}
            </div>
            <br />
          </div>
        );
      })}

      <div className="clear-left">
        <Pagination total={count} page={page} perPage={56}></Pagination>
      </div>
    </div>
  );
};

export default PhotoListComponent;
