import axios from "axios";
import { getToken } from "./auth";

const API_BASE_URL = "/api";

// Create axios instance with auth interceptor
const api = axios.create({
  baseURL: API_BASE_URL,
});

// Add auth header to all requests
api.interceptors.request.use(
  (config) => {
    const token = getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export const getPhotos = async () => {
  const response = await api.get("/photos");
  return response.data;
};

export const getPhoto = async (id) => {
  const response = await api.get(`/photos/${id}`);
  return response.data;
};

export const uploadPhoto = async (file) => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await api.post("/photos/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return response.data;
};

export const deletePhoto = async (id) => {
  const response = await api.delete(`/photos/${id}`);
  return response.data;
};
