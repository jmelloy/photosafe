import api from "./client";
import type { Photo } from "../types/api";
import type { PaginatedPhotosResponse } from "./photos";

export interface SearchFilters {
  places?: string[];
  labels?: string[];
  keywords?: string[];
  persons?: string[];
  albums?: string[];
  libraries?: string[];
  search_text?: string;
  start_date?: string;
  end_date?: string;
}

export interface AvailableSearchFilters {
  places: string[];
  labels: string[];
  keywords: string[];
  persons: string[];
  albums: string[];
  libraries: string[];
}

export const getSearchFilters = async (): Promise<AvailableSearchFilters> => {
  const response = await api.get<AvailableSearchFilters>("/search/filters");
  return response.data;
};

export const searchPhotos = async (
  page: number = 1,
  pageSize: number = 50,
  filters?: SearchFilters
): Promise<PaginatedPhotosResponse> => {
  const params: any = { page, page_size: pageSize };

  // Add filter parameters if provided
  if (filters) {
    // Convert arrays to comma-separated strings
    if (filters.places && filters.places.length > 0) {
      params.places = filters.places.join(",");
    }
    if (filters.labels && filters.labels.length > 0) {
      params.labels = filters.labels.join(",");
    }
    if (filters.keywords && filters.keywords.length > 0) {
      params.keywords = filters.keywords.join(",");
    }
    if (filters.persons && filters.persons.length > 0) {
      params.persons = filters.persons.join(",");
    }
    if (filters.albums && filters.albums.length > 0) {
      params.albums = filters.albums.join(",");
    }
    if (filters.libraries && filters.libraries.length > 0) {
      params.libraries = filters.libraries.join(",");
    }
    if (filters.search_text) {
      params.search_text = filters.search_text;
    }
    if (filters.start_date) {
      params.start_date = filters.start_date;
    }
    if (filters.end_date) {
      params.end_date = filters.end_date;
    }
  }

  const response = await api.get<PaginatedPhotosResponse>("/search/", {
    params,
  });
  return response.data;
};
