import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import Login from "./pages/Login";
import StudentDashboard from "./pages/student/Dashboard";
import AdminDashboard from "./pages/admin/AdminDashboard";
import Events from "./pages/Events";
import Notifications from "./pages/Notifications";
import StudentServices from "./pages/StudentServices";
import Communications from "./pages/Communications";
import AdminRadar from "./pages/AdminRadar";
import AdminRequests from "./pages/admin/AdminRequests";
import AdminEvents from "./pages/admin/AdminEvents";

import ProtectedRoute from "./routes/ProtectedRoute";
import RoleRoute from "./routes/RoleRoute";
import { AuthProvider, useAuth } from "./context/AuthContext";

// Redirect component to check role and route accordingly
const DashboardRedirect = () => {
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

  const role = user.role || "";
  if (role.toLowerCase() === "admin") {
    return <Navigate to="/admin" replace />;
  } else {
    return <Navigate to="/student" replace />;
  }
};

function App() {
  return (
    <AuthProvider>
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
        <Route
          path="/admin/requests"
          element={
            <ProtectedRoute>
              <RoleRoute allowedRole="Admin">
                <AdminRequests />
              </RoleRoute>
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/events"
          element={
            <ProtectedRoute>
              <RoleRoute allowedRole="Admin">
                <AdminEvents />
              </RoleRoute>
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
    </AuthProvider>
  );
}

export default App;