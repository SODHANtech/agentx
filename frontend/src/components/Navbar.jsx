import { useState, useEffect } from "react";
import { Wifi, WifiOff, UserCircle2 } from "lucide-react";
import { getDashboard } from "../services/api";

function Navbar() {

  const [isConnected, setIsConnected] = useState(false);
  const [student, setStudent] = useState({
    name: "Loading...",
    role: "Student"
  });

  useEffect(() => {

    const loadDashboard = async () => {

      try {

        const data = await getDashboard();

        setIsConnected(true);

        setStudent({
          name: data.student.name,
          role: "AI Campus User"
        });

      } catch (err) {

        setIsConnected(false);

      }

    };

    loadDashboard();

    const interval = setInterval(
      loadDashboard,
      5000
    );

    return () => clearInterval(interval);

  }, []);

  return (

    <div className="h-20 px-8 border-b border-slate-800 flex items-center justify-between bg-slate-900">

      {/* Left */}

      <div>

        <h1 className="text-2xl font-bold text-white">

          Smart Campus AI

        </h1>

        <p className="text-sm text-slate-400">

          Multi-Agent Control Center

        </p>

      </div>

      {/* Right */}

      <div className="flex items-center gap-8">

        <div
          className={`flex items-center gap-2 ${
            isConnected
              ? "text-green-400"
              : "text-red-400"
          }`}
        >

          {isConnected ? (
            <>
              <Wifi
                size={18}
                className="animate-pulse"
              />
              <span>Backend Connected</span>
            </>
          ) : (
            <>
              <WifiOff size={18} />
              <span>Backend Offline</span>
            </>
          )}

        </div>

        <div className="flex items-center gap-3">

          <UserCircle2
            size={38}
            className="text-cyan-400"
          />

          <div>

            <p className="font-semibold text-white">

              {student.name}

            </p>

            <p className="text-xs text-slate-400">

              {student.role}

            </p>

          </div>

        </div>

      </div>

    </div>

  );

}

export default Navbar;