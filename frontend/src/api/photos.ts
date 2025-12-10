import api from "./client";
import type { Photo } from "../types/api";

export interface PaginatedPhotosResponse {
  items: Photo[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

export const getPhotos = async (
  page: number = 1,
  pageSize: number = 50
): Promise<PaginatedPhotosResponse> => {
  console.log(
    `[photos.ts] getPhotos() called with page=${page}, pageSize=${pageSize}`
  );
  const response = await api.get<PaginatedPhotosResponse>("/photos/", {
    params: { page, page_size: pageSize },
  });
  console.log(
    "[photos.ts] getPhotos() response received:",
    response.data?.items?.length,
    "photos, has_more:",
    response.data?.has_more
  );
  return response.data;
};

export const getPhoto = async (id: string): Promise<Photo> => {
  const response = await api.get<Photo>(`/photos/${id}`);
  return response.data;
};

export const uploadPhoto = async (file: File): Promise<Photo> => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await api.post<Photo>("/photos/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return response.data;
};

export const deletePhoto = async (id: string): Promise<void> => {
  await api.delete(`/photos/${id}`);
};
