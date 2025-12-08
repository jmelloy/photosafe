import axios, {
  AxiosInstance,
  InternalAxiosRequestConfig,
  AxiosError,
} from "axios";

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
    // Log all API requests for debugging
    console.log(
      `[API Request] ${config.method?.toUpperCase()} ${config.baseURL}${
        config.url
      }`,
      {
        headers: config.headers,
        data: config.data,
      }
    );
    return config;
  },
  (error: AxiosError) => {
    console.error("[API Request Error]", error);
    return Promise.reject(error);
  }
);

// Add response interceptor for debugging
api.interceptors.response.use(
  (response) => {
    console.log(
      `[API Response] ${response.config.method?.toUpperCase()} ${
        response.config.url
      }`,
      {
        status: response.status,
        data: response.data,
      }
    );
    return response;
  },
  (error: AxiosError) => {
    console.error(
      `[API Response Error] ${error.config?.method?.toUpperCase()} ${
        error.config?.url
      }`,
      {
        status: error.response?.status,
        data: error.response?.data,
        message: error.message,
      }
    );
    return Promise.reject(error);
  }
);

export default api;
