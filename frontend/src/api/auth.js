import axios from "axios";

const API_BASE_URL = "/api";
const TOKEN_KEY = "photosafe_auth_token";

// Token management
export const getToken = () => {
  return localStorage.getItem(TOKEN_KEY);
};

export const setToken = (token) => {
  localStorage.setItem(TOKEN_KEY, token);
};

export const removeToken = () => {
  localStorage.removeItem(TOKEN_KEY);
};

export const isAuthenticated = () => {
  return !!getToken();
};

// API calls
export const login = async (username, password) => {
  const formData = new FormData();
  formData.append("username", username);
  formData.append("password", password);

  const response = await axios.post(`${API_BASE_URL}/auth/login`, formData, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  });

  const { access_token } = response.data;
  setToken(access_token);
  return response.data;
};

export const register = async (username, email, password, name = "") => {
  const response = await axios.post(`${API_BASE_URL}/auth/register`, {
    username,
    email,
    password,
    name,
  });
  return response.data;
};

export const getCurrentUser = async () => {
  const response = await axios.get(`${API_BASE_URL}/auth/me`);
  return response.data;
};

export const logout = () => {
  removeToken();
};
