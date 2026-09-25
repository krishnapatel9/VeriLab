import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { LogOut, LayoutDashboard, Upload } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const navItems = [];
  if (user?.role === "uploader" || user?.role === "admin") {
    navItems.push({ label: "Upload", path: "/", icon: Upload });
  }
  if (user?.role === "reviewer" || user?.role === "doctor" || user?.role === "admin") {
    navItems.push({ label: "Reports", path: "/reports", icon: LayoutDashboard });
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Global Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <span className="text-xl font-bold text-slate-900 tracking-tight">Verilab</span>
                <span className="ml-2 px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 uppercase tracking-wide">
                  {user?.role}
                </span>
              </div>
              <nav className="hidden sm:ml-8 sm:flex sm:space-x-8">
                {navItems.map((item) => {
                  const isActive = location.pathname === item.path || (item.path !== "/" && location.pathname.startsWith(item.path));
                  const Icon = item.icon;
                  return (
                    <button
                      key={item.path}
                      onClick={() => navigate(item.path)}
                      className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                        isActive
                          ? "border-blue-500 text-slate-900"
                          : "border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700"
                      }`}
                    >
                      <Icon className="w-4 h-4 mr-2" />
                      {item.label}
                    </button>
                  );
                })}
              </nav>
            </div>
            <div className="flex items-center">
              <button
                onClick={handleLogout}
                className="inline-flex items-center gap-2 px-3 py-2 border border-transparent text-sm font-medium rounded-md text-slate-500 hover:text-slate-700 hover:bg-slate-50"
              >
                <LogOut className="w-4 h-4" />
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 w-full max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <Outlet />
      </main>
    </div>
  );
}
