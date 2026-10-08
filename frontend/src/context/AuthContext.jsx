import React, { createContext, useContext, useState, useEffect } from "react";
import { login as apiLogin, logout as apiLogout, getMe } from "../services/api";

const AuthContext = createContext(null);

const DEFAULT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjIsIm5hbWUiOiJTYXR5YSIsInJvbGUiOiJTdHVkZW50IiwiZXhwIjoxNzkwNTAyMDA2fQ.oJ2QQ6mhXIQLN5kt3zAmY9LAMFjbLfoK9ciMmSwIg-Q";
const DEFAULT_USER = { id: 2, name: "Satya", email: "satya@campus.edu", role: "Student", cgpa: 8.2, backlogs: 0 };

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem("user");
    return stored ? JSON.parse(stored) : DEFAULT_USER;
  });
  const [token, setToken] = useState(() => {
    return localStorage.getItem("access_token") || DEFAULT_TOKEN;
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!localStorage.getItem("access_token")) {
      localStorage.setItem("access_token", DEFAULT_TOKEN);
      localStorage.setItem("user", JSON.stringify(DEFAULT_USER));
    }
  }, []);

  const login = async (email, password) => {
    const data = await apiLogin(email, password);
    if (data && data.access_token) {
      setToken(data.access_token);
      setUser(data.user);
    }
    return data;
  };

  const logout = () => {
    apiLogout();
    setToken(null);
    setUser(null);
  };

  const isAdmin = user?.role?.toLowerCase() === "admin";

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout, isAdmin }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
