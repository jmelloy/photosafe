import axios, { AxiosInstance, InternalAxiosRequestConfig, AxiosError } from "axios";

const API_BASE_URL = "/api";

// Create axios instance with base URL
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
});

// Token management
export const getToken = (): string | null => {
  return localStorage.getItem("photosafe_auth_token");
};

export const setToken = (token: string): void => {
  localStorage.setItem("photosafe_auth_token", token);
};

export const removeToken = (): void => {
  localStorage.removeItem("photosafe_auth_token");
};

// Add auth header to all requests
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

export default api;
