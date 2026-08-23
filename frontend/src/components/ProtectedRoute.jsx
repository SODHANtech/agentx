import React from "react";
import { Navigate } from "react-router-dom";

function ProtectedRoute({ children, requiredRole }) {
  const token = localStorage.getItem("access_token");
  
  if (!token) {
    // If no JWT token is stored, redirect to Login
    return <Navigate to="/login" replace />;
  }

  if (requiredRole) {
    try {
      const payloadBase64 = token.split(".")[1];
      const decodedPayload = JSON.parse(atob(payloadBase64.replace(/-/g, "+").replace(/_/g, "/")));
      if (decodedPayload.role !== requiredRole) {
        // Forbidden: redirect to home dashboard
        return <Navigate to="/" replace />;
      }
    } catch (e) {
      console.error("Token decoding failed in ProtectedRoute:", e);
      return <Navigate to="/login" replace />;
    }
  }
  
  return children;
}

export default ProtectedRoute;
