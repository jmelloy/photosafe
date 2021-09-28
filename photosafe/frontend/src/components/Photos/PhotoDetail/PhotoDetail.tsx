import React, { FunctionComponent, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { usePhotoService } from "../../../services/photo-service";
import { Photo } from "../../../types/Photo";
import "./PhotoDetail.css";

type Params = {
  photoId: string;
};

const PhotoComponent: FunctionComponent = () => {
  const [photo, setPhoto] = useState<Photo>();

  const photoService = usePhotoService();
  const params: Params = useParams();
  const photoId = params.photoId;

  useEffect(() => {
    const getPhotoDetail = async () => {
      const photo = await photoService.getPhotoDetail(photoId);
      setPhoto(photo);
    };
    getPhotoDetail();
  }, [photoService, photoId]);

  if (!photo) return <div className="placeholder">Hi</div>;

  return (
    <div className="flex-1 flex items-stretch overflow-hidden">
      <main className="flex-1 overflow-y-auto">
        {/* Primary column */}
        <section
          aria-labelledby="primary-heading"
          className="min-w-0 flex-1 h-full flex flex-col overflow-hidden lg:order-last"
        >
          <h1 id="primary-heading">{photo.title || photo.original_filename}</h1>
          <h2>{photo.place?.name}</h2>
          <img
            src={`https://photos.melloy.life/images/${
              photo.s3_edited_path || photo.s3_key_path
            }`}
            alt={photo.title}
          />
        </section>
      </main>

      {/* Secondary column (hidden on smaller screens) */}
      <aside className="hidden w-96 bg-white border-l border-gray-200 overflow-y-auto lg:block">
        <pre>{JSON.stringify(photo, null, 2)}</pre>
      </aside>
    </div>
  );
};

export default PhotoComponent;
