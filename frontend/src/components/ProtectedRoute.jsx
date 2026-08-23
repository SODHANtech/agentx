import React from "react";
import { Navigate } from "react-router-dom";

function ProtectedRoute({ children }) {
  const token = localStorage.getItem("access_token");
  
  if (!token) {
    // If no JWT token is stored, redirect to Login
    return <Navigate to="/login" replace />;
  }
  
  return children;
}

export default ProtectedRoute;
