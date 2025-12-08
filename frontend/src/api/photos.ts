import api from "./client";
import type { Photo } from "../types/api";

export const getPhotos = async (): Promise<Photo[]> => {
  const response = await api.get<Photo[]>("/photos/");
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
