import React, {
  FunctionComponent,
  useState,
  useEffect,
  ChangeEvent,
} from "react";
import { Photo } from "../../types/Photo";
import LoadingSpinner from "../LoadingSpinner/LoadingSpinner";

import { usePhotoService } from "../../services/photo-service";
import { useParams } from "react-router-dom";
import PhotoListComponent from "./PhotoList/PhotoList";
import Pagination from "../Pagination";
import PhotoDayComponent from "./PhotoDayComponent/PhotoDayComponent";

type Params = {
  page: string;
};

const PhotoComponent: FunctionComponent = () => {
  const [count, setCount] = useState<number>(0);
  const [photos, setPhotos] = useState<Photo[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const photoService = usePhotoService();

  const params: Params = useParams();
  const page = parseInt(params.page, 10) || 1;

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
    } catch (err: Error | unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError(`${err}`);
      }
    } finally {
      setLoading(false);
    }
  };

  const doSearch = (event: ChangeEvent<HTMLInputElement>) => {
    const searchQuery = event.target.value;
  };

  useEffect(() => {
    getPhotos();
  }, [page]);

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
    <div className="flex-1 flex items-stretch overflow-hidden">
      <main className="flex-1 overflow-y-auto">
        {/* Primary column */}
        <section
          aria-labelledby="primary-heading"
          className="min-w-0 flex-1 h-full flex flex-col overflow-hidden lg:order-last"
        >
          <h1 id="primary-heading" className="sr-only">
            Photos
          </h1>

          <div>
            <div className="clear-left">
              <Pagination total={count} page={page} perPage={56}></Pagination>
            </div>

            {errorText}
            {loadingSpinner}
            <PhotoListComponent photos={photos}></PhotoListComponent>

            <div className="clear-left">
              <Pagination total={count} page={page} perPage={56}></Pagination>
            </div>
          </div>
        </section>
      </main>

      {/* Secondary column (hidden on smaller screens) */}
      <aside className="hidden w-48 bg-white border-l border-gray-200 overflow-y-auto lg:block">
        <div>
          <label
            htmlFor="search"
            className="block text-sm font-medium text-gray-700"
          >
            Search
          </label>
          <div className="mt-1">
            <input
              type="text"
              name="search"
              id=""
              className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
              onChange={doSearch}
            />
          </div>
        </div>
        <div>
          <PhotoDayComponent></PhotoDayComponent>
        </div>
      </aside>
    </div>
  );
};

export default PhotoComponent;
