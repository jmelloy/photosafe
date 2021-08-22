import { createContext, useContext } from "react";
import makeRequest from "./make-request";
import { PhotoList } from "../types/Photo";
import config from "../config";
import { useAuth } from "./auth-service";

type PhotoContext = {
  getPhotoList: () => Promise<PhotoList>;
};

const defaults: PhotoContext = {
  getPhotoList: () =>
    Promise.resolve({ count: 0, next: "", previous: "", results: [] }),
};

const PhotoContext = createContext(defaults);

export const GalleryProvider = ({ children }: { children: any }) => {
  const auth = useAuth();
  const token = auth.getToken();

  const getPhotoList = () =>
    makeRequest<PhotoList>(`${config.baseUrl}/api/photos`, {
      headers: { authorization: `Token ${token}` },
    });

  const value = {
    getPhotoList,
  };

  return (
    <PhotoContext.Provider value={value}>{children}</PhotoContext.Provider>
  );
};

export const useGallery = () => {
  return useContext(PhotoContext);
};
