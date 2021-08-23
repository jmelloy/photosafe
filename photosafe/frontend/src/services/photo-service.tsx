import { createContext, useContext, FunctionComponent } from "react";
import makeRequest from "./make-request";
import { PhotoList, Photo } from "../types/Photo";
import config from "../config";
import { useAuth } from "./auth-service";

type PhotoContext = {
  getPhotoList: (offset: number, limit: number) => Promise<PhotoList>;
  getPhotoDetail: (photoId: string) => Promise<Photo | null>;
};

const defaults: PhotoContext = {
  getPhotoList: () =>
    Promise.resolve({ count: 0, next: "", previous: "", results: [] }),
  getPhotoDetail: () => Promise.resolve(null),
};

const PhotoServiceContext = createContext(defaults);

export const PhotoListProvider: FunctionComponent = ({ children }) => {
  const auth = useAuth();
  const token = auth.getToken();

  const getPhotoList = async (offset: number = 0, limit: number = 100) => {
    return makeRequest<PhotoList>(
      `${config.baseUrl}/api/photos/?offset=${offset}&limit=${limit}`,
      {
        headers: { authorization: `Token ${token}` },
      }
    );
  };

  const getPhotoDetail = async (photoId: string) =>
    makeRequest<Photo>(`${config.baseUrl}/api/photos/${photoId}/`, {
      headers: { authorization: `Token ${token}` },
    });

  const value = {
    getPhotoList,
    getPhotoDetail,
  };

  return (
    <PhotoServiceContext.Provider value={value}>
      {children}
    </PhotoServiceContext.Provider>
  );
};

export const usePhotoService = () => {
  return useContext(PhotoServiceContext);
};
