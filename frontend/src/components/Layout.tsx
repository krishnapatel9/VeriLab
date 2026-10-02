import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { LogOut, LayoutList, Upload } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { ROLES, isRoleKey } from "../roles";
import { Wordmark } from "./Brand";

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const role = user && isRoleKey(user.role) ? ROLES[user.role] : null;

  const nav = [
    ...(user?.role === "uploader" || user?.role === "admin" ? [{ label: "Upload", to: "/", icon: Upload, end: true }] : []),
    { label: "Reports", to: "/reports", icon: LayoutList, end: false },
  ];

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-20 border-b border-line bg-paper/85 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-[1400px] items-center justify-between px-6">
          <div className="flex items-center gap-10">
            <button onClick={() => navigate(role?.home ?? "/")} aria-label="Home">
              <Wordmark />
            </button>
            <nav className="flex items-center gap-1">
              {nav.map(({ label, to, icon: Icon, end }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={end}
                  className={({ isActive }) =>
                    `inline-flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-medium transition ${
                      isActive ? "bg-ink text-white" : "text-ink-2 hover:bg-line/60 hover:text-ink"
                    }`
                  }
                >
                  <Icon className="h-4 w-4" /> {label}
                </NavLink>
              ))}
            </nav>
          </div>
          <div className="flex items-center gap-3">
            {role && (
              <span className="inline-flex items-center gap-2 rounded-full border border-line bg-surface py-1 pl-1.5 pr-3 text-sm shadow-card">
                <span className="grid h-6 w-6 place-items-center rounded-full bg-brand text-white">
                  <role.Icon className="h-3.5 w-3.5" />
                </span>
                <span className="font-medium">{role.label}</span>
              </span>
            )}
            <button
              onClick={() => {
                logout();
                navigate("/login");
              }}
              className="btn-quiet !border-transparent !bg-transparent !px-2.5 text-ink-2 hover:!bg-line/60"
              aria-label="Sign out"
              title="Sign out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto w-full max-w-[1400px] flex-1 px-6 py-10">
        <Outlet />
      </main>
    </div>
  );
}
