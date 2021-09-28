import React, { FunctionComponent, useEffect, useState } from "react";
import { usePhotoService } from "../../../services/photo-service";
import { PhotoCount } from "../../../types/Photo";

const PhotoDayComponent: FunctionComponent = () => {
  const [photoCount, setPhotoCount] = useState<PhotoCount[]>([]);

  const [yearCount, setYearCounts] = useState<{}>({});

  const photoService = usePhotoService();

  useEffect(() => {
    const getPhotoCount = async () => {
      const results = await photoService.getPhotoDayView();
      setPhotoCount(results);
      let counts: {
        [year: number]: { [month: number]: { [day: number]: number } };
      } = {};

      results.forEach((el) => {
        if (counts[el.year]) {
          if (counts[el.year][el.month]) {
            counts[el.year][el.month][el.day] = el.count;
          } else {
            counts[el.year][el.month] = { [el.day]: el.count };
          }
        } else {
          counts[el.year] = { [el.month]: { [el.day]: el.count } };
        }
      });
      console.log(counts);
      setYearCounts(counts);
    };
    getPhotoCount();
  }, [photoService]);

  return (
    <div>
      <ul>
        {Object.keys(yearCount)
          .sort()
          .map((year) => (
            <li key={year}>{year}</li>
          ))}
      </ul>
    </div>
  );
};

export default PhotoDayComponent;
