import { createContext, useContext, FunctionComponent } from "react";
import makeRequest from "./make-request";
import { PhotoList, Photo } from "../types/Photo";
import config from "../config";
import { useAuth } from "./auth-service";

const defaultPhoto = {
  uuid: "",
  masterFingerprint: "",

  filename: "",
  original_filename: "",
  date: new Date(),
  description: "",
  title: "",
  keywords: [],
  labels: [],
  albums: [],
  folders: {},
  persons: [],
  faces: {},
  path: "",

  ismissing: false,
  hasadjustments: false,
  external_edit: false,
  favorite: false,
  hidden: false,
  latitude: 0,
  longitude: 0,
  path_edited: "",
  shared: false,
  isphoto: false,
  ismovie: false,
  uti: "",
  uti_original: "",
  burst: false,
  live_photo: false,
  path_live_photo: "",
  iscloudasset: false,
  incloud: false,
  date_modified: new Date(),
  portrait: false,
  screenshot: false,
  slow_mo: false,
  time_lapse: false,
  hdr: false,
  selfie: false,
  panorama: false,
  has_raw: false,
  israw: false,
  raw_original: false,
  uti_raw: "",
  path_raw: "",
  place: {},
  exif: {},
  score: {},
  intrash: false,
  height: 0,
  width: 0,
  orientation: 0,
  original_height: 0,
  original_width: 0,
  original_orientation: 0,
  original_filesize: 0,
  comments: {},
  likes: {},
  search_info: {},

  s3_key_path: "",
  s3_thumbnail_path: "",
  s3_edited_path: "",
};

type PhotoContext = {
  getPhotoList: (offset: number, limit: number) => Promise<PhotoList>;
  getPhotoDetail: (photoId: string) => Promise<Photo>;
};

const defaults: PhotoContext = {
  getPhotoList: () =>
    Promise.resolve({ count: 0, next: "", previous: "", results: [] }),
  getPhotoDetail: () => Promise.resolve(defaultPhoto),
};

const PhotoServiceContext = createContext(defaults);

export const PhotoListProvider: FunctionComponent = ({ children }) => {
  const auth = useAuth();
  const token = auth.getToken();

  const getPhotoList = (offset: number = 0, limit: number = 100) =>
    makeRequest<PhotoList>(
      `${config.baseUrl}/api/photos/?offset=${offset}&limit=${limit}`,
      {
        headers: { authorization: `Token ${token}` },
      }
    );

  const getPhotoDetail = (photoId: string) =>
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
