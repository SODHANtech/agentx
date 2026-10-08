import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function RoleRoute({ children, allowedRole }) {
  const { user, token, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-400 flex items-center justify-center font-mono">
        Verifying Session...
      </div>
    );
  }
  
  if (!token || !user) {
    return <Navigate to="/login" replace />;
  }

  const userRole = user.role || "";
  
  if (userRole.toLowerCase() !== allowedRole.toLowerCase()) {
    if (userRole.toLowerCase() === "admin") {
      return <Navigate to="/admin" replace />;
    } else {
      return <Navigate to="/student" replace />;
    }
  }

  return children;
}

export default RoleRoute;
