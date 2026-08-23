import React from "react";
import { Navigate } from "react-router-dom";

function RoleRoute({ children, allowedRole }) {
  const token = localStorage.getItem("access_token");
  
  if (!token) {
    return <Navigate to="/login" replace />;
  }

  try {
    const payloadBase64 = token.split(".")[1];
    const decodedPayload = JSON.parse(atob(payloadBase64.replace(/-/g, "+").replace(/_/g, "/")));
    const userRole = decodedPayload.role || "";
    
    if (userRole.toLowerCase() !== allowedRole.toLowerCase()) {
      // Forbidden: redirect to their corresponding default page
      if (userRole.toLowerCase() === "admin") {
        return <Navigate to="/admin" replace />;
      } else {
        return <Navigate to="/student" replace />;
      }
    }
  } catch (e) {
    console.error("Token decoding failed in RoleRoute:", e);
    return <Navigate to="/login" replace />;
  }

  return children;
}

export default RoleRoute;
