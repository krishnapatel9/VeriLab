import { createContext, useContext, useState, useEffect, useMemo, ReactNode } from "react";
import { jwtDecode } from "jwt-decode";
import { apiClient } from "../api/client";

interface User {
  sub: string;
  role: string;
  tenant_id: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (token: string) => void;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(localStorage.getItem("verilab_token"));

  // Derived synchronously from the token, so a navigate() right after login() already sees the user.
  const user = useMemo<User | null>(() => {
    if (!token) return null;
    try {
      const decoded = jwtDecode<User & { exp?: number }>(token);
      return decoded.exp && decoded.exp * 1000 < Date.now() ? null : decoded;
    } catch {
      return null;
    }
  }, [token]);

  useEffect(() => {
    if (token && !user) {
      localStorage.removeItem("verilab_token");
      setToken(null);
    }
    if (token && user) apiClient.defaults.headers.common["Authorization"] = `Bearer ${token}`;
    else delete apiClient.defaults.headers.common["Authorization"];
  }, [token, user]);

  const login = (newToken: string) => {
    localStorage.setItem("verilab_token", newToken);
    setToken(newToken);
  };

  const logout = () => {
    localStorage.removeItem("verilab_token");
    setToken(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
