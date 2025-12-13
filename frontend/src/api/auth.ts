import api, {
  getToken,
  setToken,
  removeToken,
  getRefreshToken,
  setRefreshToken,
} from "./client";
import type { User } from "../types/api";
import type { TokenResponse } from "../types/auth";

export { getToken, setToken, removeToken, getRefreshToken, setRefreshToken };

export const isAuthenticated = (): boolean => {
  return !!getToken();
};

// API calls
export const login = async (
  username: string,
  password: string
): Promise<TokenResponse> => {
  const formData = new URLSearchParams();
  formData.append("username", username);
  formData.append("password", password);

  const response = await api.post<TokenResponse>("/auth/login", formData, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  });

  const { access_token, refresh_token } = response.data;
  setToken(access_token);
  setRefreshToken(refresh_token);
  return response.data;
};

export const register = async (
  username: string,
  email: string,
  password: string,
  name: string = ""
): Promise<User> => {
  const response = await api.post<User>("/auth/register", {
    username,
    email,
    password,
    name,
  });
  return response.data;
};

export const getCurrentUser = async (): Promise<User> => {
  const response = await api.get<User>("/auth/me");
  return response.data;
};

export const refreshAccessToken = async (): Promise<TokenResponse> => {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    throw new Error("No refresh token available");
  }

  const response = await api.post<TokenResponse>("/auth/refresh", {
    refresh_token: refreshToken,
  });

  const { access_token, refresh_token: new_refresh_token } = response.data;
  setToken(access_token);
  setRefreshToken(new_refresh_token);
  return response.data;
};

export const logout = (): void => {
  removeToken();
};
