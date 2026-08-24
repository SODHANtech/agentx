import React, { createContext, useContext, useState, useEffect } from "react";
import { login as apiLogin, logout as apiLogout, getMe } from "../services/api";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem("access_token"));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initializeAuth = async () => {
      const storedToken = localStorage.getItem("access_token");
      const storedUser = localStorage.getItem("user");
      
      if (storedToken) {
        setToken(storedToken);
        if (storedUser) {
          try {
            setUser(JSON.parse(storedUser));
          } catch (e) {
            console.error("Failed to parse stored user:", e);
          }
        }
        try {
          const freshUser = await getMe();
          setUser(freshUser);
          localStorage.setItem("user", JSON.stringify(freshUser));
        } catch (err) {
          console.error("Token verification failed:", err);
        }
      } else {
        setUser(null);
        setToken(null);
      }
      setLoading(false);
    };

    initializeAuth();
  }, [token]);

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
