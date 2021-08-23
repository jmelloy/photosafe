import { createContext, FunctionComponent, useContext, useState } from "react";
import makeRequest from "./make-request";
import { User, TokenResponse } from "../types/User";
import config from "../config";
const baseUrl = config.baseUrl;

type AuthContext = {
  getToken: () => string | null;
  getUser: () => User | null;
  isAuthenticated: () => boolean;
  handleLogin: (username: string, password: string) => Promise<void>;
  handleLogout: () => void;
};

const defaults: AuthContext = {
  getToken: () => null,
  getUser: () => null,
  isAuthenticated: () => false,
  handleLogin: () => Promise.resolve(),
  handleLogout: () => {},
};

const AuthServiceContext = createContext(defaults);

export const AuthProvider: FunctionComponent = ({ children }) => {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);

  const getToken = () => token;
  const getUser = () => user;
  const isAuthenticated = () => !!token;

  const handleLogin = async (username: string, password: string) => {
    const tokenResponse = await makeRequest<TokenResponse>(
      `${baseUrl}/auth-token/`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username: username,
          password: password,
        }),
      }
    );
    const token = tokenResponse.token;
    setToken(token);

    const user = await makeRequest<User>(`${baseUrl}/users/me`, {
      headers: {
        authorization: `Token ${token}`,
      },
    });

    setUser(user);
  };

  const handleLogout = (): void => {
    setToken(null);
    setUser(null);
  };

  const value = {
    getUser,
    getToken,
    isAuthenticated,
    handleLogin,
    handleLogout,
  };

  return (
    <AuthServiceContext.Provider value={value}>
      {children}
    </AuthServiceContext.Provider>
  );
};

export const useAuth = () => {
  return useContext(AuthServiceContext);
};
