import React, { FunctionComponent } from "react";
import { Photo } from "../../../types/Photo";
import PhotoThumbnailComponent from "../PhotoThumbnail/PhotoThumbnail";
import { Link } from "react-router-dom";

type PhotoComponentProps = {
  photos: Photo[];
};

const PhotoListComponent: FunctionComponent<PhotoComponentProps> = ({
  photos,
}) => {
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
      {dates.map((date: string) => {
        let firstPhoto = photos.find(
          (x) => new Date(x.date).toDateString() === date
        );

        return (
          <div
            className="clear-left"
            key={`${date} - ${firstPhoto?.place?.name}`}
          >
            <h3>
              {date} - {firstPhoto?.place?.name}
            </h3>
            <div className="row-span-full">
              {photos
                .filter((x) => new Date(x.date).toDateString() === date)
                .map((photo) => (
                  <Link to={`/photos/${photo.uuid}`} key={photo.uuid}>
                    <PhotoThumbnailComponent
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
    </div>
  );
};

export default PhotoListComponent;
