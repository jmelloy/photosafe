import api from "./client";
import type { Photo } from "../types/api";

export interface PaginatedPhotosResponse {
  items: Photo[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

export interface PhotoFilters {
  search?: string;
  album?: string;
  keyword?: string;
  person?: string;
  start_date?: string;
  end_date?: string;
  favorite?: boolean;
  isphoto?: boolean;
  ismovie?: boolean;
  screenshot?: boolean;
  panorama?: boolean;
  portrait?: boolean;
  has_location?: boolean;
}

export interface AvailableFilters {
  albums: string[];
  keywords: string[];
  persons: string[];
}

export const getPhotos = async (
  page: number = 1,
  pageSize: number = 50,
  filters?: PhotoFilters
): Promise<PaginatedPhotosResponse> => {
  const params: any = { page, page_size: pageSize };
  
  // Add filter parameters if provided
  if (filters) {
    if (filters.search) params.search = filters.search;
    if (filters.album) params.album = filters.album;
    if (filters.keyword) params.keyword = filters.keyword;
    if (filters.person) params.person = filters.person;
    if (filters.start_date) params.start_date = filters.start_date;
    if (filters.end_date) params.end_date = filters.end_date;
    if (filters.favorite !== undefined) params.favorite = filters.favorite;
    if (filters.isphoto !== undefined) params.isphoto = filters.isphoto;
    if (filters.ismovie !== undefined) params.ismovie = filters.ismovie;
    if (filters.screenshot !== undefined) params.screenshot = filters.screenshot;
    if (filters.panorama !== undefined) params.panorama = filters.panorama;
    if (filters.portrait !== undefined) params.portrait = filters.portrait;
    if (filters.has_location !== undefined) params.has_location = filters.has_location;
  }
  
  const response = await api.get<PaginatedPhotosResponse>("/photos/", {
    params,
  });
  return response.data;
};

export const getAvailableFilters = async (): Promise<AvailableFilters> => {
  const response = await api.get<AvailableFilters>("/photos/filters/");
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
