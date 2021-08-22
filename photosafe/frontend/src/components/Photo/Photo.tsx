import React, { FunctionComponent } from "react";
import { Photo } from "../../types/Photo";

type PhotoComponentProps = {
  photo: Photo;
};

const PhotoComponent: FunctionComponent<PhotoComponentProps> = ({ photo }) => {
  return (
    <div>
      <img src="{photo.s3_thumbnail_key}" alt="{photo.caption}" />
    </div>
  );
};

export default PhotoComponent;
