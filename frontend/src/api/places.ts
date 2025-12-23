import api from "./client";
import type { PlaceSummary } from "../types/api";

export interface PlaceSummaryFilters {
  country?: string;
  state_province?: string;
  limit?: number;
  offset?: number;
}

export const getPlaceSummaries = async (
  filters?: PlaceSummaryFilters
): Promise<PlaceSummary[]> => {
  const params: any = {};

  if (filters) {
    if (filters.country) params.country = filters.country;
    if (filters.state_province) params.state_province = filters.state_province;
    if (filters.limit !== undefined) params.limit = filters.limit;
    if (filters.offset !== undefined) params.offset = filters.offset;
  }

  const response = await api.get<PlaceSummary[]>("/place-summaries", {
    params,
  });
  return response.data;
};

export const getPlaceSummary = async (id: number): Promise<PlaceSummary> => {
  const response = await api.get<PlaceSummary>(`/place-summaries/${id}`);
  return response.data;
};
