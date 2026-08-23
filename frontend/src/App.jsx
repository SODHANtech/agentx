import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import Login from "./pages/Login";
import StudentDashboard from "./pages/student/Dashboard";
import AdminDashboard from "./pages/admin/AdminDashboard";
import Events from "./pages/Events";
import Notifications from "./pages/Notifications";
import StudentServices from "./pages/StudentServices";
import Communications from "./pages/Communications";
import AdminRadar from "./pages/AdminRadar";

import ProtectedRoute from "./routes/ProtectedRoute";
import RoleRoute from "./routes/RoleRoute";

// Redirect component to check role and route accordingly
const DashboardRedirect = () => {
  const token = localStorage.getItem("access_token");
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  try {
    const payloadBase64 = token.split(".")[1];
    const decodedPayload = JSON.parse(atob(payloadBase64.replace(/-/g, "+").replace(/_/g, "/")));
    const role = decodedPayload.role || "";
    
    if (role.toLowerCase() === "admin") {
      return <Navigate to="/admin" replace />;
    } else {
      return <Navigate to="/student" replace />;
    }
  } catch (e) {
    console.error("Token decoding failed in DashboardRedirect:", e);
    return <Navigate to="/login" replace />;
  }
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        
        {/* Dynamic landing selector */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <DashboardRedirect />
            </ProtectedRoute>
          }
        />

        {/* Student Dashboard */}
        <Route
          path="/student"
          element={
            <ProtectedRoute>
              <RoleRoute allowedRole="Student">
                <StudentDashboard />
              </RoleRoute>
            </ProtectedRoute>
          }
        />

        {/* Admin Dashboard */}
        <Route
          path="/admin"
          element={
            <ProtectedRoute>
              <RoleRoute allowedRole="Admin">
                <AdminDashboard />
              </RoleRoute>
            </ProtectedRoute>
          }
        />

        {/* Student Features */}
        <Route
          path="/events"
          element={
            <ProtectedRoute>
              <RoleRoute allowedRole="Student">
                <Events />
              </RoleRoute>
            </ProtectedRoute>
          }
        />
        <Route
          path="/notifications"
          element={
            <ProtectedRoute>
              <RoleRoute allowedRole="Student">
                <Notifications />
              </RoleRoute>
            </ProtectedRoute>
          }
        />
        <Route
          path="/student-services"
          element={
            <ProtectedRoute>
              <RoleRoute allowedRole="Student">
                <StudentServices />
              </RoleRoute>
            </ProtectedRoute>
          }
        />
        <Route
          path="/communications"
          element={
            <ProtectedRoute>
              <Communications />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin-radar"
          element={
            <ProtectedRoute>
              <RoleRoute allowedRole="Admin">
                <AdminRadar />
              </RoleRoute>
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;