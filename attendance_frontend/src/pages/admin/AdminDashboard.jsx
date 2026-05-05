import {
  Routes,
  Route,
  Link,
  useNavigate,
  useLocation,
} from "react-router-dom";
import { useContext } from "react";
import { AuthContext } from "../../context/AuthContext";
import { LayoutDashboard, Users, CalendarCheck, LogOut } from "lucide-react";

// Sub-components (We will build these next)
import DashboardStats from "./DashboardStats";
import ManageStudents from "./ManageStudents";
import LeaveApprovals from "./LeaveApprovals";

export default function AdminDashboard() {
  const { logout, user } = useContext(AuthContext);
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  const navItems = [
    { path: "/admin", icon: LayoutDashboard, label: "Overview" },
    { path: "/admin/students", icon: Users, label: "Manage Students" },
    { path: "/admin/leaves", icon: CalendarCheck, label: "Leave Requests" },
  ];

  return (
    <div className="flex h-screen p-4 gap-4 overflow-hidden">
      {/* Sidebar - Glassmorphism */}
      <div className="glass-panel w-64 flex flex-col justify-between p-4">
        <div>
          <div className="mb-8 px-4">
            <h2 className="text-2xl font-bold text-white drop-shadow-md">
              Admin Portal
            </h2>
            <p className="text-white/80 text-sm mt-1">Welcome, {user?.name}</p>
          </div>
          <nav className="space-y-2">
            {navItems.map((item) => {
              const isActive =
                location.pathname === item.path ||
                (item.path !== "/admin" &&
                  location.pathname.startsWith(item.path));
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                    isActive
                      ? "bg-white/30 text-white font-semibold shadow-inner border border-white/40"
                      : "text-white/70 hover:bg-white/10 hover:text-white"
                  }`}
                >
                  <item.icon size={20} />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 px-4 py-3 text-red-100 hover:bg-red-500/20 rounded-xl transition-colors mt-auto"
        >
          <LogOut size={20} />
          Sign Out
        </button>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 glass-panel overflow-y-auto relative">
        <div className="p-8">
          <Routes>
            <Route path="/" element={<DashboardStats />} />
            <Route path="/students" element={<ManageStudents />} />
            <Route path="/leaves" element={<LeaveApprovals />} />
          </Routes>
        </div>
      </div>
    </div>
  );
}
