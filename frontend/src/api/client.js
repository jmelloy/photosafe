import axios from "axios";

const API_BASE_URL = "/api";

// Create axios instance with base URL
const api = axios.create({
  baseURL: API_BASE_URL,
});

// Token management
export const getToken = () => {
  return localStorage.getItem("photosafe_auth_token");
};

export const setToken = (token) => {
  localStorage.setItem("photosafe_auth_token", token);
};

export const removeToken = () => {
  localStorage.removeItem("photosafe_auth_token");
};

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

export default api;
