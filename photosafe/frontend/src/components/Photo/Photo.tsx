import React, { FunctionComponent } from "react";
import { Photo } from "../../types/Photo";
import "./Photo.css";
type PhotoComponentProps = {
  photo: Photo | null;
  width: number | null;
  height: number;
};

const PhotoComponent: FunctionComponent<PhotoComponentProps> = ({
  photo,
  width = 256,
  height = 256,
}) => {
  if (photo) {
    return (
      <div className="photoholder">
        <img
          src={`https://photos.melloy.life/images/${
            photo.s3_edited_path || photo.s3_thumbnail_path || photo.s3_key_path
          }?height=${height}`}
          alt={photo.title}
          height={height}
          width={(photo.width / photo.height) * height}
        />
      </div>
    );
  }
  return <div className="placeholder">Hi</div>;
};

export default PhotoComponent;
