import api, { getToken, setToken, removeToken } from "./client";

export { getToken, setToken, removeToken };

export const isAuthenticated = () => {
  return !!getToken();
};

// API calls
export const login = async (username, password) => {
  const formData = new URLSearchParams();
  formData.append("username", username);
  formData.append("password", password);

  const response = await api.post("/auth/login", formData, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  });

  const { access_token } = response.data;
  setToken(access_token);
  return response.data;
};

export const register = async (username, email, password, name = "") => {
  const response = await api.post("/auth/register", {
    username,
    email,
    password,
    name,
  });
  return response.data;
};

export const getCurrentUser = async () => {
  const response = await api.get("/auth/me");
  return response.data;
};

export const logout = () => {
  removeToken();
};
