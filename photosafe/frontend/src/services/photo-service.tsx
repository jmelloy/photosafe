import { createContext, useContext, FunctionComponent } from "react";
import makeRequest from "./make-request";
import { PhotoList } from "../types/Photo";
import config from "../config";
import { useAuth } from "./auth-service";

type PhotoContext = {
  getPhotoList: (offset: number, limit: number) => Promise<PhotoList>;
};

const defaults: PhotoContext = {
  getPhotoList: () =>
    Promise.resolve({ count: 0, next: "", previous: "", results: [] }),
};

const PhotoServiceContext = createContext(defaults);

export const PhotoListProvider: FunctionComponent = ({ children }) => {
  const auth = useAuth();
  const token = auth.getToken();

  const getPhotoList = async (offset: number = 0, limit: number = 100) => {
    console.log(
      "url",
      `${config.baseUrl}/api/photos?offset=${offset}&limit=${limit}`
    );
    console.log("token", token);
    return makeRequest<PhotoList>(
      `${config.baseUrl}/api/photos?offset=${offset}&limit=${limit}`,
      {
        method: "GET",
        headers: { authorization: `Token ${token}` },
      }
    );
  };

  const value = {
    getPhotoList,
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
