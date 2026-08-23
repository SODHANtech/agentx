import { Link, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  Calendar,
  Bell,
  Building2,
  MessageSquare,
  LogOut
} from "lucide-react";
import { logout } from "../services/api";

function Sidebar() {
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

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