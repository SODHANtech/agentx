import { Link, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  Calendar,
  Bell,
  Building2,
  MessageSquare,
  LogOut,
  Radio,
  ClipboardList
} from "lucide-react";
import { useAuth } from "../context/AuthContext";

function Sidebar() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const role = user?.role || null;

  return (
    <div className="w-64 h-screen bg-slate-900 border-r border-slate-800/80 text-white p-5 flex flex-col justify-between">
      <div>
        <h1 className="text-2xl font-bold mb-10 tracking-tight text-white">
          Campus<span className="text-cyan-400">OS</span>
        </h1>

        <nav className="flex flex-col gap-6">
          <Link
            to="/"
            className="flex items-center gap-3 hover:text-cyan-400 text-slate-300 font-medium transition"
          >
            <LayoutDashboard size={20} />
            Dashboard
          </Link>

          {/* Student-only Links */}
          {role === "Student" && (
            <>
              <Link
                to="/events"
                className="flex items-center gap-3 hover:text-cyan-400 text-slate-300 font-medium transition"
              >
                <Calendar size={20} />
                Events
              </Link>

              <Link
                to="/notifications"
                className="flex items-center gap-3 hover:text-cyan-400 text-slate-300 font-medium transition"
              >
                <Bell size={20} />
                Notifications
              </Link>

              <Link
                to="/student-services"
                className="flex items-center gap-3 hover:text-cyan-400 text-slate-300 font-medium transition"
              >
                <Building2 size={20} />
                Student Services
              </Link>

              <Link
                to="/communications"
                className="flex items-center gap-3 hover:text-cyan-400 text-slate-300 font-medium transition"
              >
                <MessageSquare size={20} />
                Communications
              </Link>
            </>
          )}

          {/* Admin-only Links */}
          {role === "Admin" && (
            <>
              <Link
                to="/admin-radar"
                className="flex items-center gap-3 hover:text-cyan-400 text-slate-300 font-medium transition"
              >
                <Radio size={20} className="text-cyan-400" />
                Complaint Radar
              </Link>

              <Link
                to="/admin/requests"
                className="flex items-center gap-3 hover:text-cyan-400 text-slate-300 font-medium transition"
              >
                <ClipboardList size={20} className="text-cyan-400" />
                Requests Admin
              </Link>

              <Link
                to="/admin/events"
                className="flex items-center gap-3 hover:text-cyan-400 text-slate-300 font-medium transition"
              >
                <Calendar size={20} className="text-cyan-400" />
                Events Admin
              </Link>
            </>
          )}
        </nav>
      </div>

      <button
        onClick={handleLogout}
        className="flex items-center gap-3 hover:text-red-400 text-slate-400 font-medium pt-5 border-t border-slate-800/80 w-full text-left transition"
      >
        <LogOut size={20} />
        Sign Out
      </button>
    </div>
  );
}

export default Sidebar;